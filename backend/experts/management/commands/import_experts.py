import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from experts.importer import CSVImportError, MAX_BYTES, import_csv

class Command(BaseCommand):
    help = 'Validate and import a synthetic UTF-8 registry. Existing IDs are updated; --replace clears the old registry atomically.'

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=Path)
        parser.add_argument('--replace', action='store_true')

    def handle(self, *args, **options):
        try:
            path = options['csv_path']
            if path.stat().st_size > MAX_BYTES:
                raise CSVImportError('Файл больше 5 МБ.')
            result = import_csv(path.read_bytes(), replace=options['replace'])
        except (OSError, CSVImportError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps(result, ensure_ascii=False))
