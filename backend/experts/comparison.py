"""Local comparison grounded in the existing search results."""
import json
import re
import socket
from time import perf_counter
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Expert
from .rag_facts import comparative_facts
from .search.multilingual import language_of
from .search.engine import SearchEngine
from .serializers import ExpertSerializer, SearchRequestSerializer


def complete_comparison(answer, ids):
    legacy_citations = set(re.findall(r'\bEXP-[0-9]+\b', answer))
    if not legacy_citations.issubset(set(ids)):
        return False
    prose = answer
    for expert_id in sorted(ids, key=len, reverse=True):
        pattern = rf'(?<![A-Za-z0-9_-]){re.escape(expert_id)}(?![A-Za-z0-9_-])'
        if not re.search(pattern, answer):
            return False
        prose = re.sub(pattern, '', prose)
    sentences = [part for part in re.split(r'[.!?]+(?:\s|$)', prose) if len(re.findall(r'[^\W\d_]+', part, re.UNICODE)) >= 3]
    return 2 <= len(sentences) <= 4



@api_view(['POST'])
def compare(request):
    serializer = SearchRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    values = dict(serializer.validated_data)
    values['limit'] = 3
    payload = SearchEngine(Expert.objects.all()).search(**values)
    facts = []
    for candidate in payload['results']:
        facts.append({
            'expert': ExpertSerializer(candidate['expert']).data,
            'explanation': candidate['explanation'],
            'missing_requirements': candidate['missing_requirements'],
            'warnings': candidate['warnings'],
        })
    ids = [fact['expert']['id'] for fact in facts]
    if not facts:
        return Response({'status': 'no_matches', 'expert_ids': [], 'detail': 'Нет экспертов для сравнения.'})
    language = language_of(values['query'])
    verified = comparative_facts(facts, language)
    properties = {key: {'type': 'string', 'enum': [text]} for key, text in verified.items()}
    body = {
        'model': settings.OLLAMA_MODEL,
        'stream': False,
        'format': {'type': 'object', 'properties': properties, 'required': list(properties), 'additionalProperties': False},
        'messages': [
            {'role': 'system', 'content': f'Compare only the supplied verified facts in language {language}. Return the exact grounded JSON schema. Never invent IDs, skills or suitability claims.'},
            {'role': 'user', 'content': json.dumps({'language': language, 'comparison': verified}, ensure_ascii=False)},
        ],
        'options': {'temperature': 0, 'num_predict': 600},
    }
    try:
        started = perf_counter()
        req = Request(settings.OLLAMA_URL.rstrip('/') + '/api/chat', data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
        with urlopen(req, timeout=settings.OLLAMA_TIMEOUT) as response:
            raw = json.load(response)
            structured = json.loads(raw['message']['content'])
            sentences = [structured[key] for key in verified]
            answer = ' '.join(text.strip().rstrip('.!?') + '.' for text in sentences)
        metadata = {'model': raw.get('model', settings.OLLAMA_MODEL), 'elapsed_ms': round((perf_counter() - started) * 1000), 'language': language}
        if any(structured[key] != text for key, text in verified.items()) or not complete_comparison(answer, ids):
            return Response({'status': 'invalid_response', 'expert_ids': ids, 'detail': 'ИИ вернул неполное сравнение. Повторите попытку или используйте факты в карточках.', **metadata})
        return Response({'status': 'ok', 'comparison': answer, 'expert_ids': ids, **metadata})
    except (URLError, TimeoutError, socket.timeout, OSError, ValueError, KeyError, TypeError):
        return Response({'status': 'unavailable', 'expert_ids': ids, 'detail': 'Локальный ИИ недоступен или превысил время ожидания. Карточки экспертов доступны.'})
