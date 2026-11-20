from time import perf_counter

from django.db import DatabaseError, connection
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Expert
from .search.engine import SearchEngine
from .search.taxonomy import INDUSTRIES
from .serializers import ExpertSerializer, SearchRequestSerializer

@api_view(['GET'])
def health(request):
    try:
        count = Expert.objects.count()
    except DatabaseError:
        return Response({'status': 'database_not_ready', 'hint': 'Run migrate and import_experts.'}, status=503)
    return Response({'status': 'ok' if count >= 100 else 'registry_not_ready', 'expert_count': count,
                     'offline': True, 'database': connection.vendor, 'is_synthetic': True,
                     'version': '0.1.0'}, status=200 if count >= 100 else 503)

@api_view(['POST'])
def search(request):
    started = perf_counter()
    serializer = SearchRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    values = serializer.validated_data
    engine = SearchEngine(Expert.objects.all())
    if not engine.experts:
        return Response({'status': 'registry_empty', 'detail': 'Загрузите CSV командой import_experts.'}, status=503)
    payload = engine.search(**values)
    for result in payload['results']:
        result['expert'] = ExpertSerializer(result['expert']).data
    payload['elapsed_ms'] = round((perf_counter() - started) * 1000, 3)
    return Response(payload)

@api_view(['GET'])
def industries(request):
    return Response({'industries': list(INDUSTRIES), 'is_synthetic': True})

@api_view(['GET'])
def expert_detail(request, expert_id):
    return Response(ExpertSerializer(get_object_or_404(Expert, pk=expert_id)).data)

@api_view(['GET'])
def experts(request):
    try:
        offset = int(request.query_params.get('offset', 0))
        limit = int(request.query_params.get('limit', 20))
    except ValueError:
        return Response({'detail': 'offset и limit должны быть целыми числами.'}, status=400)
    if offset < 0 or not 1 <= limit <= 100:
        return Response({'detail': 'offset >= 0, 1 <= limit <= 100.'}, status=400)
    queryset = Expert.objects.all()
    industry = request.query_params.get('industry')
    if industry:
        if industry not in INDUSTRIES:
            return Response({'detail': 'Неизвестная отрасль.'}, status=400)
        queryset = queryset.filter(industry=industry)
    return Response({'count': queryset.count(), 'offset': offset, 'limit': limit,
                     'results': ExpertSerializer(queryset[offset:offset + limit], many=True).data, 'is_synthetic': True})
