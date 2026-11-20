"""Offline BM25 + canonical skills/constraints. No evaluation labels are used here."""
import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from threading import local

import snowballstemmer

from .taxonomy import CITIES, INDUSTRIES, SKILLS, STOPWORDS

STEMMERS = local()
TOKEN_PATTERN = re.compile(r'[a-zа-яё0-9]+', re.I)

@lru_cache(maxsize=8192)
def stem(token):
    if not hasattr(STEMMERS, 'ru'):
        STEMMERS.ru = snowballstemmer.stemmer('russian')
        STEMMERS.en = snowballstemmer.stemmer('english')
    return (STEMMERS.ru if re.search('[а-я]', token) else STEMMERS.en).stemWord(token)

def tokens(text):
    text = unicodedata.normalize('NFKC', text).lower().replace('ё', 'е')
    return [stem(word) for word in TOKEN_PATTERN.findall(text)]

STOP_STEMS = {stem(word) for word in STOPWORDS}

def lexical_tokens(text):
    return [word for word in tokens(text) if word not in STOP_STEMS]

@lru_cache(maxsize=1)
def alias_tables():
    return tuple({key: [tuple(tokens(alias)) for alias in [key, *aliases]] for key, aliases in table.items()}
                 for table in (SKILLS, INDUSTRIES, CITIES))

def detect(query_tokens, table):
    found, consumed = [], set()
    for key, aliases in table.items():
        for alias in aliases:
            if any(tuple(query_tokens[i:i + len(alias)]) == alias for i in range(len(query_tokens) - len(alias) + 1)):
                found.append(key)
                consumed.update(alias)
                break
    return found, consumed

def canonical_skill(value):
    normalized = tuple(tokens(value))
    return next((key for key, aliases in alias_tables()[0].items() if normalized in aliases), value.strip())

@dataclass(frozen=True)
class ParsedQuery:
    skills: tuple
    industries: tuple
    cities: tuple
    min_years: int | None
    excluded_skills: tuple
    keywords: tuple
    unrecognized_terms: tuple

    def as_dict(self):
        return {'skills': list(self.skills), 'industries': list(self.industries), 'cities': list(self.cities),
                'min_years_experience': self.min_years, 'excluded_skills': list(self.excluded_skills),
                'unrecognized_terms': list(self.unrecognized_terms)}

def parse_query(query):
    query_tokens = tokens(query)
    skill_table, industry_table, city_table = alias_tables()
    skills, skill_terms = detect(query_tokens, skill_table)
    industries, industry_terms = detect(query_tokens, industry_table)
    cities, city_terms = detect(query_tokens, city_table)
    # A generic mention of production is not an instruction to exclude pharma/automation.
    pharma_skills = {'GMP', 'GCP', 'Клинические исследования', 'Фармаконадзор', 'Валидация процессов', 'Аудит производства', 'Регистрация лекарств'}
    automation_skills = {'PLC', 'SCADA', 'OPC UA', 'Промышленный IoT', 'Робототехника', 'Безопасность АСУ ТП'}
    if 'Производство' in industries and (set(skills) & (pharma_skills | automation_skills) or len(industries) > 1):
        industries.remove('Производство')
    excluded = []
    for phrase in re.findall(r'(?:без\s+|не\s+нуж(?:ен|на|ны)\s+)([^,.!?;]+)', query.lower()):
        found, _ = detect(tokens(phrase), skill_table)
        excluded.extend(found)
    skills = [skill for skill in skills if skill not in excluded]
    exp_match = re.search(r'(?:от|минимум|не менее|не меньше|более|свыше|at least)\s*(\d{1,2})\s*(?:лет|год|years?)', query.lower())
    if not exp_match:
        exp_match = re.search(r'(\d{1,2})\s*\+\s*(?:лет|год|years?)', query.lower())
    min_years = int(exp_match.group(1)) if exp_match else None
    if exp_match and re.match(r'(?:более|свыше)', exp_match.group(0)):
        min_years += 1
    consumed = skill_terms | industry_terms | city_terms | STOP_STEMS
    if exp_match:
        consumed.update(tokens(exp_match.group(0)))
    raw_words = TOKEN_PATTERN.findall(unicodedata.normalize('NFKC', query).lower().replace('ё', 'е'))
    unknown = tuple(dict.fromkeys(word for word in raw_words if stem(word) not in consumed))
    return ParsedQuery(tuple(skills), tuple(industries), tuple(cities), min_years,
                       tuple(dict.fromkeys(excluded)), tuple(dict.fromkeys(lexical_tokens(query))), unknown)

class BM25:
    def __init__(self, documents, k1=1.5, b=0.75):
        self.counts = [Counter(document) for document in documents]
        self.lengths = [len(document) for document in documents]
        self.avg = sum(self.lengths) / max(1, len(documents)) or 1
        self.df = Counter(word for document in self.counts for word in document)
        self.size, self.k1, self.b = len(documents), k1, b

    def score(self, query, position):
        frequencies = self.counts[position]
        value = 0.0
        for term in set(query):
            frequency = frequencies.get(term, 0)
            if not frequency:
                continue
            idf = math.log(1 + (self.size - self.df[term] + .5) / (self.df[term] + .5))
            norm = self.k1 * (1 - self.b + self.b * self.lengths[position] / self.avg)
            value += idf * frequency * (self.k1 + 1) / (frequency + norm)
        return value

class SearchEngine:
    """Immutable per-request index; 100–150 profiles don't need a cache or vector DB.

    Extension point: a future local embedding reranker can score these same candidates.
    It must preserve constraints, evidence and the completely offline baseline fallback.
    """
    def __init__(self, experts):
        self.experts = list(experts)
        self.profile_skills = [{canonical_skill(s) for s in expert.skills} for expert in self.experts]
        documents = []
        for expert in self.experts:
            expanded = ' '.join(' '.join(SKILLS.get(skill, [])) for skill in expert.skills)
            text = ' '.join([' '.join(expert.skills)] * 3 + [expert.title] * 2 +
                            [expert.bio, expert.industry, expert.city, expanded])
            documents.append(lexical_tokens(text))
        self.bm25 = BM25(documents)

    def search(self, query, limit=3, industry=None):
        parsed = parse_query(query)
        results = []
        for i, expert in enumerate(self.experts):
            if industry and expert.industry != industry:
                continue
            profile = self.profile_skills[i]
            if set(parsed.excluded_skills) & profile:
                continue
            matched = [skill for skill in parsed.skills if skill in profile]
            missing = [skill for skill in parsed.skills if skill not in profile]
            lexical = self.bm25.score(parsed.keywords, i)
            # Explicit named skills are required evidence, not just incidental city overlap.
            if parsed.skills and not matched:
                continue
            if not parsed.skills and lexical <= 0:
                continue
            if not parsed.skills and parsed.unrecognized_terms and not (set(tokens(' '.join(parsed.unrecognized_terms))) & self.bm25.counts[i].keys()):
                # A known city alone must not manufacture expertise in an unknown specialty.
                continue
            city_ok = not parsed.cities or expert.city in parsed.cities
            industry_ok = not parsed.industries or expert.industry in parsed.industries
            experience_ok = parsed.min_years is None or expert.years_experience >= parsed.min_years
            skill_fraction = len(matched) / len(parsed.skills) if parsed.skills else 0
            constraints = [(city_ok, 1)] if parsed.cities else []
            if parsed.industries:
                constraints.append((industry_ok, 1))
            if parsed.min_years is not None:
                constraints.append((experience_ok, 1))
            # Only recognized explicit requirements enter coverage. This is NOT a probability.
            total_weight = len(parsed.skills) * 2 + sum(weight for _, weight in constraints)
            met_weight = len(matched) * 2 + sum(weight for passed, weight in constraints if passed)
            coverage = round(100 * met_weight / total_weight, 1) if total_weight else None
            full_match = bool(total_weight) and not missing and city_ok and industry_ok and experience_ok
            ranking = 60 * skill_fraction + 20 * lexical / (lexical + 4)
            ranking += (6 if city_ok else -18) if parsed.cities else 0
            ranking += (6 if industry_ok else -15) if parsed.industries else 0
            ranking += (3 if experience_ok else -10) if parsed.min_years is not None else 0
            availability_penalty = {'available': 0, 'limited': 3, 'busy': 8}[expert.availability]
            ranking -= availability_penalty
            missing_requirements = list(missing)
            if not city_ok:
                missing_requirements.append('Город: ' + ' / '.join(parsed.cities))
            if not industry_ok:
                missing_requirements.append('Отрасль: ' + ' / '.join(parsed.industries))
            if not experience_ok:
                missing_requirements.append(f'Опыт от {parsed.min_years} лет')
            matched_keywords = sorted(set(parsed.keywords) & self.bm25.counts[i].keys())
            reasons = []
            if matched:
                reasons.append('В профиле указаны компетенции: ' + ', '.join(matched) + '.')
            reasons.append(f'Отрасль профиля: {expert.industry}.')
            if parsed.cities and city_ok:
                reasons.append(f'Город соответствует запросу: {expert.city}.')
            if parsed.min_years is not None and experience_ok:
                reasons.append(f'Опыт {expert.years_experience} лет соответствует указанному минимуму.')
            if not matched:
                reasons.append('Найдено лексическое совпадение с текстом профиля; требуется проверка компетенций.')
            warnings = list(missing_requirements)
            if expert.availability != 'available':
                warnings.append('Доступность: ' + expert.get_availability_display() + '.')
            results.append({
                'expert': expert, 'score': round(ranking, 4), 'match_percent': coverage,
                'match_status': 'full' if full_match else 'partial',
                'matched_skills': matched, 'matched_industries': [expert.industry] if industry_ok and parsed.industries else [],
                'profile_industry': expert.industry, 'missing_requirements': missing_requirements,
                'explanation': reasons, 'warnings': warnings,
                'score_components': {'bm25': round(lexical, 4), 'skill_coverage': round(skill_fraction, 4),
                                     'availability_penalty': availability_penalty},
                # Matching term stems are diagnostic, not user-facing competence claims.
                'matched_terms': matched_keywords,
            })
        # Hard requirements are a tier: busy exact experts outrank free but unsuitable ones.
        results.sort(key=lambda r: (r['match_status'] == 'full', r['score'], r['expert'].id), reverse=True)
        selected = results[:limit]
        status = 'no_matches' if not selected else ('ok' if selected[0]['match_status'] == 'full' else 'partial')
        warnings = []
        if status == 'partial':
            warnings.append('Полного соответствия распознанным требованиям нет. Показаны частичные совпадения.')
        if status == 'no_matches':
            warnings.append('Релевантные эксперты не найдены. Уточните компетенции или снимите отраслевой фильтр.')
        if any(r['match_status'] == 'partial' for r in selected) and status == 'ok':
            warnings.append('Часть кандидатов соответствует запросу не полностью; проверьте missing_requirements.')
        if parsed.unrecognized_terms:
            warnings.append('Часть слов обработана только лексически. Процент покрывает распознанные требования, а не весь смысл запроса.')
        if not parsed.skills:
            warnings.append('Компетенции из словаря не распознаны: используется лексический поиск по профилям.')
        return {'query': query, 'status': status, 'parsed_query': parsed.as_dict(), 'results': selected,
                'warnings': warnings, 'candidate_count': len(results), 'total_experts': len(self.experts),
                'method': 'bm25+skill-taxonomy-v1', 'semantic_embeddings_used': False,
                'score_description': 'Ранжирующий балл, не вероятность. match_percent — доля распознанных требований: компетенция весит 2, город/отрасль/опыт по 1.',
                'is_synthetic': True}
