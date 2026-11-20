from django.test import SimpleTestCase
from experts.comparison import complete_comparison

class ComparisonValidationTests(SimpleTestCase):
    def test_ids_alone_are_incomplete(self):
        self.assertFalse(complete_comparison('1. EXP-014\n2. EXP-004\n3. EXP-010', ['EXP-014', 'EXP-004', 'EXP-010']))

    def test_prose_with_all_citations(self):
        text = 'EXP-014 имеет опыт работы в фармацевтике и доступен. EXP-004 также имеет GMP и доступен в Шымкенте.'
        self.assertTrue(complete_comparison(text, ['EXP-014', 'EXP-004']))
        self.assertFalse(complete_comparison(text, ['EXP-014']))

    def test_csv_custom_ids(self):
        answer = 'CSV_CUSTOM-7 имеет GMP и восемь лет опыта. CSV_OTHER имеет GMP и десять лет опыта.'
        self.assertTrue(complete_comparison(answer, ['CSV_CUSTOM-7', 'CSV_OTHER']))
