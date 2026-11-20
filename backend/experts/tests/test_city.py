from unittest.mock import patch
from urllib.error import URLError
from django.test import TestCase
from rest_framework.test import APIClient
from experts.importer import import_csv
from experts.synthetic import generate_rows
from experts.importer import CSV_FIELDS
import csv
import io

class CityFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(generate_rows())
        import_csv(stream.getvalue().encode())

    def test_city_filter_and_rag_share_top_three(self):
        client = APIClient()
        body = {'query': 'GMP', 'city': 'Алматы', 'limit': 20}
        response = client.post('/api/v1/search/', body, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['results'])
        self.assertTrue(all(row['expert']['city'] == 'Алматы' for row in response.data['results']))
        self.assertEqual(response.data['parsed_query']['cities'], ['Алматы'])
        with patch('experts.comparison.urlopen', side_effect=URLError('offline')):
            comparison = client.post('/api/v1/compare/', body, format='json')
        self.assertEqual(comparison.data['expert_ids'], [row['expert']['id'] for row in response.data['results'][:3]])

    def test_conflict_rejected_for_both_endpoints(self):
        for endpoint in ['search', 'compare']:
            response = APIClient().post(f'/api/v1/{endpoint}/', {'query': 'GMP, не из Алматы', 'city': 'Алматы'}, format='json')
            self.assertEqual(response.status_code, 400)
            self.assertIn('Противоречие', str(response.data))

    def test_find_experts_from_city(self):
        response = APIClient().post('/api/v1/search/', {'query': 'Найди экспертов из Алматы', 'limit':20}, format='json')
        self.assertTrue(response.data['results'])
        self.assertNotIn('найди', response.data['parsed_query']['unrecognized_terms'])
        self.assertTrue(all(row['expert']['city'] == 'Алматы' for row in response.data['results']))
