"""Privacy-preserving global demand and current registry supply."""
from collections import Counter
from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Expert, SearchTotals, SkillDemand
from .search.engine import canonical_skill

@transaction.atomic
def record_search(skills):
    SearchTotals.objects.get_or_create(pk=1)
    totals = SearchTotals.objects.select_for_update().get(pk=1)
    now = timezone.now()
    totals.started_at = totals.started_at or now
    totals.last_request_at = now
    totals.request_count += 1
    for skill in sorted({canonical_skill(skill) for skill in skills}):
        demand, _ = SkillDemand.objects.get_or_create(skill=skill)
        demand.request_count += 1
        demand.save(update_fields=['request_count'])
    totals.save()

@api_view(['GET'])
@transaction.atomic
def analytics(request):
    totals = SearchTotals.objects.select_for_update().filter(pk=1).first()
    industry = request.query_params.get('industry') or None
    selected_skill = request.query_params.get('skill') or None
    experts = list(Expert.objects.all())
    industries = sorted({expert.industry for expert in experts})
    if industry and industry not in industries:
        return Response({'detail': 'Неизвестная отрасль реестра.'}, status=400)
    demand = dict(SkillDemand.objects.values_list('skill', 'request_count'))
    all_skills = sorted(set(demand) | {canonical_skill(skill) for expert in experts for skill in expert.skills})
    if selected_skill and selected_skill not in all_skills:
        return Response({'detail': 'Неизвестная компетенция.'}, status=400)
    supply = Counter()
    sectors = {}
    scoped_experts = []
    for expert in experts:
        skills = {canonical_skill(skill) for skill in expert.skills}
        if industry and expert.industry != industry:
            continue
        if expert.availability == 'available':
            supply.update(skills)
        if selected_skill and selected_skill not in skills:
            continue
        scoped_experts.append(expert)
        sector = sectors.setdefault(expert.industry, {'industry': expert.industry, 'available': 0, 'limited': 0, 'busy': 0, 'total': 0})
        sector[expert.availability] += 1
        sector['total'] += 1
    rows = [{'skill': skill, 'requests': count, 'available_experts': supply[skill]}
            for skill, count in sorted(demand.items(), key=lambda item: (-item[1], item[0]))
            if not selected_skill or skill == selected_skill]
    total_requests = totals.request_count if totals else 0
    return Response({
        'total_requests': total_requests,
        'filtered_requests': demand.get(selected_skill, 0) if selected_skill else total_requests,
        'period_start': totals.started_at if totals else None, 'period_end': timezone.now(),
        'skills': rows[:5], 'table': rows, 'competencies': all_skills, 'industries': industries,
        'availability_by_industry': [sectors[key] for key in sorted(sectors)],
        'expert_count': len(scoped_experts),
        'available_expert_count': sum(expert.availability == 'available' for expert in scoped_experts),
        'filters': {'industry': industry, 'skill': selected_skill},
        'demand_scope': 'global', 'is_synthetic': True,
    })
