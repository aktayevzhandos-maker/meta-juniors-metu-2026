"""Localized, verifiable comparative statements for the local model."""
from .search.multilingual import skill_label

STATUS = {
    'ru': {'available': 'Доступен', 'limited': 'Ограниченно доступен', 'busy': 'Занят'},
    'kk': {'available': 'Қолжетімді', 'limited': 'Қолжетімділігі шектеулі', 'busy': 'Бос емес'},
    'en': {'available': 'Available', 'limited': 'Limited availability', 'busy': 'Busy'},
}
LABELS = {
    'ru': ['Общие компетенции выбранных экспертов', 'Опыт работы, в годах', 'Различия, влияющие на выбор', 'только общие компетенции', 'Не совпало с условиями', 'Недостающих распознанных условий нет'],
    'kk': ['Таңдалған сарапшылардың ортақ құзыреттері', 'Жылмен көрсетілген еңбек өтілі', 'Таңдауға әсер ететін айырмашылықтар', 'тек ортақ құзыреттер', 'Сәйкес келмеген талаптар', 'Танылған талаптардың барлығы орындалған'],
    'en': ['Shared competencies across the selected experts', 'Work experience expressed in years', 'Differences that affect the choice', 'shared competencies only', 'Unmet requirements', 'All recognized requirements are satisfied'],
}


def missing_label(value, language):
    if language == 'ru':
        return value
    replacements = {
        'en': {'Опыт не более ': 'Experience at most ', 'Опыт от ': 'Experience at least ', ' лет': ' years', 'Город: ': 'City: ', 'Отрасль: ': 'Industry: '},
        'kk': {'Опыт не более ': 'Еңбек өтілі ең көбі ', 'Опыт от ': 'Еңбек өтілі кемінде ', ' лет': ' жыл', 'Город: ': 'Қала: ', 'Отрасль: ': 'Сала: '},
    }
    text = value
    for source, target in replacements[language].items():
        text = text.replace(source, target)
    return skill_label(text, language)


def comparative_facts(facts, language):
    labels = LABELS[language]
    shared = sorted(set.intersection(*(set(fact['expert']['skills']) for fact in facts)))
    ids = [fact['expert']['id'] for fact in facts]
    no_shared = {'ru': 'отсутствуют', 'kk': 'жоқ', 'en': 'none'}[language]
    common = f"{labels[0]} ({', '.join(ids)}): {', '.join(skill_label(skill, language) for skill in shared) or no_shared}"
    experience = labels[1] + ': ' + ', '.join(f"{fact['expert']['id']} — {fact['expert']['years_experience']}" for fact in facts)
    groups = {}
    for fact in facts:
        extra = tuple(skill for skill in fact['expert']['skills'] if skill not in shared)
        groups.setdefault(extra, []).append(fact['expert']['id'])
    differences = labels[2] + ': ' + '; '.join(
        f"{', '.join(group_ids)} — {', '.join(skill_label(skill, language) for skill in skills) or labels[3]}"
        for skills, group_ids in groups.items()
    )
    statuses = '; '.join(f"{fact['expert']['id']} — {STATUS[language][fact['expert']['availability']]}" for fact in facts)
    missing = [f"{fact['expert']['id']} — {', '.join(missing_label(value, language) for value in fact['missing_requirements'])}"
               for fact in facts if fact['missing_requirements']]
    limitations = statuses + '; ' + (labels[4] + ': ' + '; '.join(missing) if missing else labels[5])
    return {'common': common, 'experience': experience, 'differences': differences, 'limitations': limitations}
