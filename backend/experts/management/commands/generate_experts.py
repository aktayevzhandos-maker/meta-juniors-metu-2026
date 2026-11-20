from pathlib import Path
from django.core.management.base import BaseCommand
from experts.synthetic import write_registry

class Command(BaseCommand):
    help = 'Write 120 deterministic synthetic expert profiles to UTF-8 CSV.'

    def add_arguments(self, parser):
        parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[4] / 'data' / 'experts.csv')
        parser.add_argument('--seed', type=int, default=2026)

    def handle(self, *args, **options):
        count = write_registry(options['output'], options['seed'])
        self.stdout.write(f'Generated {count} synthetic profiles: {options["output"]}')
