import csv
import io
import json
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from experts.importer import CSV_FIELDS, CSVImportError, import_csv, parse_csv
from experts.models import Expert
from experts.search.engine import SearchEngine, canonical_skill, parse_query
from experts.synthetic import generate_rows

ROOT = Path(__file__).resolve().parents[3]

def csv_bytes(rows, bom=False):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    return (('\ufeff' if bom else '') + stream.getvalue()).encode('utf-8')

class RegistryTests(TestCase):
    def test_generator_is_deterministic_diverse_and_synthetic(self):
        rows = generate_rows()
        self.assertEqual(rows, generate_rows())
        self.assertEqual(len(rows), 120)
        self.assertEqual(len({row['id'] for row in rows}), 120)
        self.assertEqual(len({row['industry'] for row in rows}), 8)
        self.assertEqual(len({row['city'] for row in rows}), 6)
        self.assertTrue(all(row['is_synthetic'] == 'true' and row['full_name'].startswith('Синтетический') for row in rows))

    def test_utf8_bom_upsert_and_idempotency(self):
        data = csv_bytes(generate_rows(), bom=True)
        self.assertEqual(import_csv(data)['created'], 120)
        self.assertEqual(import_csv(data)['updated'], 120)
        self.assertEqual(Expert.objects.count(), 120)
        self.assertEqual(Expert.objects.get(pk='EXP-001').city, 'Алматы')

    def test_replace_is_explicit_and_atomic_on_invalid_data(self):
        rows = generate_rows()[:2]
        import_csv(csv_bytes(rows))
        bad = [dict(rows[0], years_experience='bad')]
        with self.assertRaises(CSVImportError):
            import_csv(csv_bytes(bad), replace=True)
        self.assertEqual(Expert.objects.count(), 2)
        import_csv(csv_bytes(rows[:1]), replace=True)
        self.assertEqual(Expert.objects.count(), 1)

    def test_duplicate_ids_empty_skills_invalid_availability_and_non_synthetic_rejected(self):
        rows = generate_rows()[:1]
        for field, value in [('skills', ''), ('availability', 'unknown'), ('is_synthetic', 'false'),
                             ('years_experience', '-1'), ('industry', 'unknown'), ('city', ''), ('id', '=formula')]:
            with self.subTest(field=field), self.assertRaises(CSVImportError):
                parse_csv(csv_bytes([dict(rows[0], **{field: value})]))
        with self.assertRaises(CSVImportError):
            parse_csv(csv_bytes(rows + rows))
        with self.assertRaises(CSVImportError):
            parse_csv(b'id,title\n1,test\n')
        with self.assertRaises(CSVImportError):
            parse_csv(b'\xff\xfe')

    def test_invalid_late_row_does_not_update_earlier_profile(self):
        rows = generate_rows()[:2]
        import_csv(csv_bytes(rows))
        rows[0]['title'] = 'Must not be persisted'
        rows[1]['years_experience'] = 'not-a-number'
        with self.assertRaises(CSVImportError):
            import_csv(csv_bytes(rows))
        self.assertNotEqual(Expert.objects.get(pk='EXP-001').title, rows[0]['title'])

class SearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        import_csv(csv_bytes(generate_rows()))

    def setUp(self):
        self.client = APIClient()

    def search(self, query, **extra):
        response = self.client.post('/api/v1/search/', {'query': query, **extra}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def test_reference_and_paraphrase_sets_meet_hit_at_3(self):
        for filename in ['reference_queries.json', 'holdout_queries.json']:
            cases = json.loads((ROOT / 'data' / filename).read_text(encoding='utf-8'))['queries']
            hits = 0
            for case in cases:
                result = self.search(case['query'])
                ids = {item['expert']['id'] for item in result['results']}
                hits += bool(ids & set(case['relevant_ids']))
            self.assertGreaterEqual(hits / len(cases), .8, (filename, hits, len(cases)))

    def test_actual_evidence_and_missing_requirements(self):
        payload = self.search('GMP и клинические исследования в Алматы')
        for result in payload['results']:
            self.assertTrue(set(result['matched_skills']).issubset(result['expert']['skills']))
            self.assertEqual(result['profile_industry'], result['expert']['industry'])
            self.assertTrue(result['explanation'])
        first = payload['results'][0]
        self.assertEqual(first['expert']['id'], 'EXP-001')
        self.assertEqual(first['match_percent'], 100)
        self.assertEqual(first['missing_requirements'], [])
        self.assertIn('не вероятность', payload['score_description'])

    def test_busy_penalty_and_exact_match_tier(self):
        Expert.objects.all().delete()
        base = parse_csv(csv_bytes(generate_rows()[:1]))[0]
        kwargs = {field: getattr(base, field) for field in CSV_FIELDS if field != 'id'}
        Expert.objects.create(id='A', **dict(kwargs, availability='available'))
        Expert.objects.create(id='B', **dict(kwargs, availability='busy'))
        Expert.objects.create(id='C', **dict(kwargs, skills=['GMP'], availability='available'))
        results = self.search('GMP и клинические исследования в Алматы')['results']
        self.assertEqual([item['expert']['id'] for item in results], ['A', 'B', 'C'])
        self.assertEqual(results[1]['score_components']['availability_penalty'], 8)
        self.assertEqual(results[2]['match_status'], 'partial')

    def test_hard_industry_filter_and_contradictory_city(self):
        payload = self.search('GMP', industry='Качество и сертификация')
        self.assertTrue(payload['results'])
        self.assertTrue(all(item['expert']['industry'] == 'Качество и сертификация' for item in payload['results']))
        payload = self.search('GMP и клинические исследования в Караганде')
        # There is no full GMP+clinical profile in Karaganda in the registry.
        self.assertEqual(payload['status'], 'partial')
        self.assertTrue(payload['results'][0]['missing_requirements'])

    def test_experience_constraints_and_aliases(self):
        parsed = parse_query('ПЛК и СКАДА в Астане не менее 10 лет')
        self.assertEqual(set(parsed.skills), {'PLC', 'SCADA'})
        self.assertEqual(parsed.min_years, 10)
        self.assertEqual(parsed.cities, ('Астана',))
        self.assertEqual(canonical_skill('сапр'), 'CAD')
        payload = self.search('Python NLP от 30 лет')
        self.assertEqual(payload['status'], 'partial')
        self.assertIn('Опыт от 30 лет', payload['results'][0]['missing_requirements'])

    def test_unknown_specialty_does_not_return_arbitrary_city_matches(self):
        for query in ['Эксперт по археологии майя', 'Квантовая телепортация в Алматы', 'Нужен специалист по квантовой телепортации']:
            with self.subTest(query=query):
                payload = self.search(query)
                self.assertEqual(payload['status'], 'no_matches')
                self.assertEqual(payload['results'], [])

    def test_partial_and_unrecognized_query_are_disclosed(self):
        payload = self.search('GMP и SCADA')
        self.assertEqual(payload['status'], 'partial')
        self.assertLess(payload['results'][0]['match_percent'], 100)
        payload = self.search('GMP и квантовая телепортация')
        self.assertTrue(payload['parsed_query']['unrecognized_terms'])
        self.assertTrue(any('только лексически' in warning for warning in payload['warnings']))

    def test_excluded_skills(self):
        payload = self.search('Нужен SCADA без PLC')
        self.assertTrue(payload['results'])
        self.assertTrue(all('PLC' not in result['expert']['skills'] for result in payload['results']))

    def test_query_validation_and_limits(self):
        for body in [{}, {'query': ''}, {'query': '12'}, {'query': '123'}, {'query': 'x' * 1001},
                     {'query': 'GMP', 'limit': 2}, {'query': 'GMP', 'limit': 21},
                     {'query': 'GMP', 'industry': 'unknown'}]:
            with self.subTest(body=body):
                self.assertEqual(self.client.post('/api/v1/search/', body, format='json').status_code, 400)
        self.assertEqual(len(self.search('GMP', limit=5)['results']), 5)

    def test_read_endpoints_cors_and_http_methods(self):
        health = self.client.get('/api/v1/health/')
        self.assertEqual(health.json()['expert_count'], 120)
        self.assertEqual(health.status_code, 200)
        self.assertEqual(self.client.get('/api/v1/experts/').json()['count'], 120)
        self.assertEqual(self.client.get('/api/v1/experts/EXP-001/').json()['id'], 'EXP-001')
        self.assertEqual(self.client.get('/api/v1/experts/nope/').status_code, 404)
        self.assertEqual(self.client.get('/api/v1/experts/?offset=-1').status_code, 400)
        self.assertEqual(self.client.get('/api/v1/experts/?industry=unknown').status_code, 400)
        self.assertEqual(len(self.client.get('/api/v1/industries/').json()['industries']), 8)
        self.assertEqual(self.client.get('/api/v1/search/').status_code, 405)
        cors = self.client.options('/api/v1/search/', HTTP_ORIGIN='http://localhost:5173',
                                   HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST', HTTP_ACCESS_CONTROL_REQUEST_HEADERS='content-type')
        self.assertEqual(cors['Access-Control-Allow-Origin'], 'http://localhost:5173')
        foreign = self.client.get('/api/v1/health/', HTTP_ORIGIN='https://unknown.example')
        self.assertNotIn('Access-Control-Allow-Origin', foreign)

    def test_no_network_and_empty_registry_health(self):
        with patch('socket.socket.connect', side_effect=AssertionError('Network disallowed')):
            self.assertTrue(self.search('GMP')['results'])
        Expert.objects.all().delete()
        self.assertEqual(self.client.get('/api/v1/health/').status_code, 503)
        self.assertEqual(self.client.post('/api/v1/search/', {'query': 'GMP'}, format='json').status_code, 503)
