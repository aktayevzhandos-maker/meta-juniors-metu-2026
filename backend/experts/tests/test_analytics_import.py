from django.test import TestCase
from rest_framework.test import APIClient
from experts.analytics import record_search
from experts.models import Expert, SkillDemand, SearchTotals
from experts.synthetic import generate_rows
from experts.importer import CSV_FIELDS
import csv
import io

class AnalyticsTests(TestCase):
    def test_unique_skills_and_read_only_get(self):
        record_search(['GMP', 'GMP'])
        record_search([])
        self.assertEqual(SkillDemand.objects.get(skill='GMP').request_count, 1)
        self.assertEqual(SearchTotals.objects.get().request_count, 2)
        client = APIClient()
        for _ in range(2):
            response = client.get('/api/v1/analytics/')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['skills'][0]['requests'], 1)
        self.assertEqual(SearchTotals.objects.get().request_count, 2)

    def test_empty(self):
        response = APIClient().get('/api/v1/analytics/')
        self.assertEqual(response.data['skills'], [])
        self.assertIsNone(response.data['period_start'])

class CSVPreviewTests(TestCase):
    def test_preview_apply_preserves_others_and_validates_token(self):
        client = APIClient()
        rows = generate_rows()[:2]
        def content(row):
            stream = io.StringIO()
            writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerow(row)
            return stream.getvalue()
        first = content(rows[0])
        preview = client.post('/api/v1/import/', {'content': first}, format='json')
        self.assertEqual(preview.status_code, 200)
        self.assertEqual(Expert.objects.count(), 0)
        applied = client.post('/api/v1/import/', {'mode': 'apply', 'content': first, 'token': preview.data['token']}, format='json')
        self.assertEqual(applied.data['created'], 1)
        second = content(rows[1])
        bad = client.post('/api/v1/import/', {'mode': 'apply', 'content': second, 'token': preview.data['token']}, format='json')
        self.assertEqual(bad.status_code, 400)
        preview2 = client.post('/api/v1/import/', {'content': second}, format='json')
        client.post('/api/v1/import/', {'mode':'apply','content':second,'token':preview2.data['token']},format='json')
        self.assertEqual(Expert.objects.count(), 2)
        updated = client.post('/api/v1/import/', {'content': first}, format='json')
        self.assertEqual(updated.data['updated'], 1)
        self.assertEqual(updated.data['created'], 0)
