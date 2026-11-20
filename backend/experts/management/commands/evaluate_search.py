import json
import math
from pathlib import Path
from statistics import median
from time import perf_counter
from unittest.mock import patch

from django.core.management.base import BaseCommand, CommandError
from rest_framework.test import APIClient

class Command(BaseCommand):
    help = 'Evaluate end-to-end API Hit@3, no-match negatives and latency with network connections blocked.'

    def add_arguments(self, parser):
        parser.add_argument('--queries', type=Path, required=True)
        parser.add_argument('--output', type=Path)

    def handle(self, *args, **options):
        try:
            specification = json.loads(options['queries'].read_text(encoding='utf-8'))
        except (OSError, ValueError) as error:
            raise CommandError(str(error)) from error
        client, rows, latencies = APIClient(), [], []
        # APIClient runs the real view + database in-process: no HTTP overhead is claimed.
        with patch('socket.socket.connect', side_effect=AssertionError('Network prohibited during evaluation')):
            for case in specification['queries']:
                started = perf_counter()
                response = client.post('/api/v1/search/', {'query': case['query'], 'limit': 3}, format='json', HTTP_HOST='localhost')
                duration = (perf_counter() - started) * 1000
                if response.status_code != 200:
                    raise CommandError(f'{case["id"]}: HTTP {response.status_code}')
                payload = response.json()
                ids = [result['expert']['id'] for result in payload['results'][:3]]
                hit = bool(set(ids) & set(case['relevant_ids']))
                rows.append({'id': case['id'], 'query': case['query'], 'expected': case['relevant_ids'],
                             'top3': ids, 'hit': hit, 'elapsed_ms': round(duration, 3)})
                latencies.append(duration)
            negatives = []
            for query in specification.get('negative_queries', []):
                response = client.post('/api/v1/search/', {'query': query}, format='json', HTTP_HOST='localhost')
                negatives.append({'query': query, 'passed': response.status_code == 200 and not response.json()['results']})
        if not rows:
            raise CommandError('No labeled queries.')
        hit_rate = sum(row['hit'] for row in rows) / len(rows)
        report = {'dataset': options['queries'].name, 'query_count': len(rows), 'hit_at_3': hit_rate,
                  'threshold_passed': hit_rate >= .8, 'network_blocked': True,
                  'latency_scope': 'in-process Django API including PostgreSQL connection/queries, index construction and serialization; excludes HTTP transport',
                  'median_ms': round(median(latencies), 3),
                  'p95_ms': round(sorted(latencies)[math.ceil(.95 * len(latencies)) - 1], 3),
                  'max_ms': round(max(latencies), 3), 'under_30_seconds': max(latencies) < 30000,
                  'results': rows, 'negative_results': negatives,
                  'limitation': 'Team-authored synthetic data and labels. Does not establish accuracy on unseen jury queries.'}
        encoded = json.dumps(report, ensure_ascii=False, indent=2)
        self.stdout.write(encoded)
        if options['output']:
            options['output'].parent.mkdir(parents=True, exist_ok=True)
            options['output'].write_text(encoded + '\n', encoding='utf-8')
        if not report['threshold_passed'] or not report['under_30_seconds'] or not all(case['passed'] for case in negatives):
            raise CommandError('Evaluation threshold/latency/negative check failed; inspect report.')
