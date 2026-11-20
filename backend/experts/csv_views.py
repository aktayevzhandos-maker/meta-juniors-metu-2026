"""Preview and apply synthetic CSV through the existing validated importer."""
import csv
import hashlib
import io
from django.core import signing
from django.http import HttpResponse
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .importer import CSV_FIELDS, CSVImportError, parse_csv, import_csv
from .models import Expert
from .synthetic import generate_rows

@api_view(['GET'])
def template(request):
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
    writer.writeheader()
    writer.writerow(generate_rows()[0])
    response = HttpResponse('\ufeff' + output.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="synthetic-experts-template.csv"'
    return response

@api_view(['POST'])
@transaction.atomic
def csv_import(request):
    content = request.data.get('content')
    mode = request.data.get('mode', 'preview')
    if not isinstance(content, str) or len(content.encode('utf-8')) > 1024 * 1024:
        return Response({'errors': ['Выберите CSV в UTF-8 размером до 1 МБ.']}, status=400)
    if mode not in {'preview', 'apply'}:
        return Response({'errors': ['Неизвестный режим импорта.']}, status=400)
    raw = content.encode('utf-8')
    try:
        experts = parse_csv(raw)
    except CSVImportError as error:
        return Response({'errors': [str(error)]}, status=400)
    digest = hashlib.sha256(raw).hexdigest()
    if mode == 'apply':
        try:
            verified = signing.loads(request.data.get('token', ''), salt='synthetic-csv', max_age=600)
        except (signing.BadSignature, TypeError):
            return Response({'errors': ['Предпросмотр истёк. Проверьте файл ещё раз.']}, status=400)
        if verified != digest:
            return Response({'errors': ['Файл изменился. Повторите предпросмотр.']}, status=400)
        return Response({'status': 'applied', **import_csv(raw, replace=False)})
    existing = Expert.objects.filter(pk__in=[expert.pk for expert in experts]).count()
    return Response({'status': 'preview', 'created': len(experts) - existing, 'updated': existing,
                     'token': signing.dumps(digest, salt='synthetic-csv'), 'errors': [], 'is_synthetic': True})
