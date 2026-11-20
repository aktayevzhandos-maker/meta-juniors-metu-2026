from django.core.management.base import BaseCommand
from django.db import transaction
from experts.models import Expert
from experts.synthetic import generate_rows

class Command(BaseCommand):
    help = 'Rename only untouched baseline placeholder names; preserve all imported profiles and fields.'

    @transaction.atomic
    def handle(self, *args, **options):
        updated = 0
        for row in generate_rows():
            number = int(row['id'].split('-')[1])
            updated += Expert.objects.filter(pk=row['id'], full_name=f'Синтетический эксперт {number:03d}').update(full_name=row['full_name'])
        self.stdout.write(f'Updated names: {updated}; profiles retained: {Expert.objects.count()}')
