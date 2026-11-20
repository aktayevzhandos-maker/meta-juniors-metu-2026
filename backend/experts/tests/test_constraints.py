from django.test import SimpleTestCase, TestCase
from experts.search.engine import parse_query, SearchEngine
from experts.importer import parse_csv
from experts.models import Expert
from .test_backend import csv_bytes
from experts.synthetic import generate_rows

class ConstraintParsingTests(SimpleTestCase):
    def test_upper_bound_is_not_lower_bound(self):
        for phrase, expected in [('не более 10 лет',10),('не больше 10 лет',10),('до 10 лет',10),('менее 10 лет',9),('максимум 10 лет',10)]:
            with self.subTest(phrase=phrase):
                parsed=parse_query('GMP, опыт '+phrase)
                self.assertIsNone(parsed.min_years)
                self.assertEqual(parsed.max_years,expected)

    def test_lower_bounds_remain_supported(self):
        for phrase, expected in [('от 10 лет',10),('не менее 10 лет',10),('не меньше 10 лет',10),('более 10 лет',11),('свыше 10 лет',11),('10+ лет',10)]:
            with self.subTest(phrase=phrase):
                self.assertEqual(parse_query('GMP '+phrase).min_years,expected)

    def test_range_and_multiple_bounds(self):
        for phrase in ['от 5 до 10 лет','5–10 лет','от 5 лет, не более 10 лет']:
            with self.subTest(phrase=phrase):
                parsed=parse_query('GMP '+phrase)
                self.assertEqual((parsed.min_years,parsed.max_years),(5,10))
        self.assertTrue(parse_query('GMP от 20 лет до 10 лет').errors)

    def test_negative_city_is_not_positive(self):
        for phrase in ['GMP, но не из Алматы','GMP не в Алматы']:
            with self.subTest(phrase=phrase):
                parsed=parse_query(phrase)
                self.assertEqual(parsed.cities,())
                self.assertEqual(parsed.excluded_cities,('Алматы',))

    def test_exclusion_scope_and_lists(self):
        for phrase in ['Без PLC нужен специалист по SCADA','SCADA без PLC','SCADA, не нужен PLC']:
            with self.subTest(phrase=phrase):
                parsed=parse_query(phrase)
                self.assertEqual(parsed.skills,('SCADA',))
                self.assertEqual(parsed.excluded_skills,('PLC',))
        parsed=parse_query('Python без React и SQL')
        self.assertEqual(parsed.skills,('Python',))
        self.assertEqual(set(parsed.excluded_skills),{'React','SQL'})

    def test_excluded_word_is_not_unknown_or_lexical_signal(self):
        parsed=parse_query('Фармацевтика от 5 лет без Python')
        self.assertEqual(parsed.skills,())
        self.assertEqual(parsed.excluded_skills,('Python',))
        self.assertNotIn('без',parsed.unrecognized_terms)
        self.assertNotIn('python',parsed.keywords)

    def test_unfamiliar_city_is_preserved(self):
        self.assertEqual(parse_query('GMP в Ташкенте').cities,('Ташкенте',))
        self.assertEqual(parse_query('GMP в Бишкеке').cities,('Бишкеке',))

class ConstraintRankingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Expert.objects.bulk_create(parse_csv(csv_bytes(generate_rows())))

    def search(self,query):
        return SearchEngine(Expert.objects.all()).search(query)

    def test_excluded_city_never_returned(self):
        result=self.search('GMP, но не из Алматы')
        self.assertTrue(result['results'])
        self.assertTrue(all(row['expert'].city!='Алматы' for row in result['results']))

    def test_upper_bound_has_correct_evidence(self):
        result=self.search('GMP опыт не более 10 лет')
        self.assertEqual(result['status'],'ok')
        self.assertTrue(all(row['expert'].years_experience<=10 for row in result['results'] if row['match_status']=='full'))
        self.assertTrue(any('максимум' in reason for reason in result['results'][0]['explanation']))

    def test_no_experience_boundary_violation_claimed_full(self):
        for query in ['GMP от 9 до 10 лет','GMP менее 9 лет','GMP более 20 лет']:
            result=self.search(query); parsed=parse_query(query)
            for row in result['results']:
                if row['match_status']=='full':
                    self.assertGreaterEqual(row['expert'].years_experience,parsed.min_years or 0)
                    self.assertLessEqual(row['expert'].years_experience,parsed.max_years if parsed.max_years is not None else 60)

    def test_industry_only_with_exclusion_returns_candidates(self):
        result=self.search('Фармацевтика от 5 лет без Python')
        self.assertEqual(result['status'],'ok')
        self.assertTrue(result['results'])
        self.assertTrue(all(row['expert'].industry=='Фармацевтика' and 'Python' not in row['expert'].skills for row in result['results'] if row['match_status']=='full'))

    def test_unfamiliar_city_cannot_be_full(self):
        result=self.search('GMP в Бишкеке')
        self.assertEqual(result['status'],'partial')
        self.assertTrue(all(row['match_status']=='partial' and 'Город: Бишкеке' in row['missing_requirements'] for row in result['results']))

    def test_contradictory_bounds_return_no_matches_and_warning(self):
        result=self.search('GMP от 20 лет до 10 лет')
        self.assertEqual(result['status'],'no_matches')
        self.assertTrue(result['parsed_query']['errors'])
        self.assertEqual(result['results'],[])
