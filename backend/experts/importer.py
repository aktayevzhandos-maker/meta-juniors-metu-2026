"""Strict UTF-8 CSV import. Validate the whole file before changing the database."""
import csv
import io

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Expert
from .search.engine import canonical_skill
from .search.taxonomy import INDUSTRIES

CSV_FIELDS = ['id', 'full_name', 'title', 'industry', 'city', 'skills', 'languages',
              'years_experience', 'availability', 'bio', 'is_synthetic']
MAX_ROWS = 10000
MAX_BYTES = 5 * 1024 * 1024

class CSVImportError(ValueError):
    pass

def parse_csv(content):
    if len(content) > MAX_BYTES:
        raise CSVImportError('Файл больше 5 МБ.')
    try:
        text = content.decode('utf-8-sig')
    except UnicodeDecodeError as error:
        raise CSVImportError('Требуется CSV в UTF-8.') from error
    reader = csv.DictReader(io.StringIO(text, newline=''))
    if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise CSVImportError('Отсутствует заголовок или есть повторяющиеся колонки.')
    if set(reader.fieldnames) != set(CSV_FIELDS):
        raise CSVImportError('Ожидаемые колонки: ' + ','.join(CSV_FIELDS))
    experts, ids = [], set()
    try:
        for line, row in enumerate(reader, 2):
            if len(experts) >= MAX_ROWS:
                raise CSVImportError(f'Допускается до {MAX_ROWS} строк.')
            if None in row or any(value is None for value in row.values()):
                raise CSVImportError(f'Строка {line}: некорректное число колонок.')
            row = {key: value.strip() for key, value in row.items()}
            if row['id'] in ids:
                raise CSVImportError(f'Строка {line}: повторяющийся id {row["id"]}.')
            if not row['id'] or not all(char.isascii() and (char.isalnum() or char in '_-') for char in row['id']):
                raise CSVImportError(f'Строка {line}: id должен содержать ASCII буквы, цифры, _ или -.')
            if row['is_synthetic'].lower() not in {'true', '1'}:
                raise CSVImportError(f'Строка {line}: допускаются только синтетические данные.')
            if row['industry'] not in INDUSTRIES:
                raise CSVImportError(f'Строка {line}: неизвестная отрасль.')
            try:
                years = int(row['years_experience'])
            except ValueError as error:
                raise CSVImportError(f'Строка {line}: опыт должен быть целым числом.') from error
            skills = list(dict.fromkeys(canonical_skill(value.strip()) for value in row['skills'].split('|') if value.strip()))
            languages = list(dict.fromkeys(value.strip() for value in row['languages'].split('|') if value.strip()))
            if not 1 <= len(skills) <= 30 or any(len(skill) > 100 for skill in skills):
                raise CSVImportError(f'Строка {line}: требуется от 1 до 30 компетенций длиной до 100 символов.')
            if not languages or any(len(language) > 40 for language in languages):
                raise CSVImportError(f'Строка {line}: некорректный список языков.')
            if len(row['bio']) > 5000:
                raise CSVImportError(f'Строка {line}: описание длиннее 5000 символов.')
            expert = Expert(id=row['id'], full_name=row['full_name'], title=row['title'], industry=row['industry'],
                            city=row['city'], skills=skills, languages=languages, years_experience=years,
                            availability=row['availability'], bio=row['bio'], is_synthetic=True)
            try:
                expert.full_clean(validate_unique=False, validate_constraints=False)
            except ValidationError as error:
                raise CSVImportError(f'Строка {line}: {error.message_dict}') from error
            experts.append(expert)
            ids.add(expert.id)
    except csv.Error as error:
        raise CSVImportError(f'Некорректный CSV: {error}') from error
    if not experts:
        raise CSVImportError('Реестр пуст.')
    return experts

@transaction.atomic
def import_csv(content, replace=False):
    experts = parse_csv(content)
    if replace:
        Expert.objects.all().delete()
    existing = set(Expert.objects.filter(pk__in=[expert.pk for expert in experts]).values_list('pk', flat=True))
    for expert in experts:
        Expert.objects.update_or_create(pk=expert.pk, defaults={
            field: getattr(expert, field) for field in CSV_FIELDS if field != 'id'
        })
    return {'imported': len(experts), 'created': len(experts) - len(existing), 'updated': len(existing),
            'total': Expert.objects.count(), 'is_synthetic': True}
