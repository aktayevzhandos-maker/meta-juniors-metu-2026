"""Small deterministic RU/KK/EN vocabulary, not an LLM dependency."""
import re

SKILL_LABELS = {
    'GMP': ('Good manufacturing practice', 'Тиісті өндірістік практика'),
    'GCP': ('Good clinical practice', 'Тиісті клиникалық практика'),
    'NLP': ('Natural language processing', 'Табиғи тілді өңдеу'),
    'Клинические исследования': ('Clinical trials', 'Клиникалық зерттеулер'),
    'Аудит производства': ('Production audit', 'Өндірістік аудит'),
    'Валидация процессов': ('Process validation', 'Процестерді валидациялау'),
    'Регистрация лекарств': ('Drug registration', 'Дәрілерді тіркеу'),
    'Фармаконадзор': ('Pharmacovigilance', 'Фармакологиялық қадағалау'),
    'Машинное обучение': ('Machine learning', 'Машиналық оқыту'),
    'Компьютерное зрение': ('Computer vision', 'Компьютерлік көру'),
    'Промышленный IoT': ('Industrial IoT', 'Өнеркәсіптік IoT'),
    'Робототехника': ('Robotics', 'Робототехника'),
    'Предиктивное обслуживание': ('Predictive maintenance', 'Болжамды техникалық қызмет'),
    'Энергоэффективность': ('Energy efficiency', 'Энергия тиімділігі'),
    'Возобновляемая энергетика': ('Renewable energy', 'Жаңартылатын энергия'),
    'Безопасность сетей': ('Network security', 'Желілік қауіпсіздік'),
    'Безопасность АСУ ТП': ('OT security', 'Өнеркәсіптік қауіпсіздік'),
    'Охрана труда': ('Occupational safety', 'Еңбекті қорғау'),
    'Сертификация ЕАЭС': ('EAEU certification', 'ЕАЭО сертификаттау'),
    'Метрология': ('Metrology', 'Метрология'),
}


def language_of(query):
    if re.search('[әғқңөұүһі]', query, re.I) or re.search(r'\b(?:сарапшы|керек|бойынша|маман)\b', query, re.I):
        return 'kk'
    return 'ru' if re.search('[а-яё]', query, re.I) else 'en'


def skill_label(skill, language):
    if skill in {'GMP', 'GCP', 'NLP'}:
        return skill
    labels = SKILL_LABELS.get(skill)
    return labels[0 if language == 'en' else 1] if labels and language != 'ru' else skill


def normalize_query(query):
    text = query
    # Resolve inflected cities before generic Kazakh word replacements.
    cities = {'Алматы': ['Алматы', 'Almaty'], 'Астана': ['Астана', 'Astana'], 'Караганда': ['Қарағанды', 'Караганда', 'Karaganda'],
              'Шымкент': ['Шымкент', 'Shymkent'], 'Атырау': ['Атырау', 'Atyrau'], 'Павлодар': ['Павлодар', 'Pavlodar']}
    for city, names in cities.items():
        for name in names:
            text = re.sub(rf'\b{re.escape(name)}(?:дан|ден|тан|тен|да|де|та|те)\s+(?:емес|басқа)', f'не из {city}', text, flags=re.I)
            text = re.sub(rf'\b{re.escape(name)}(?:дан|ден|тан|тен|да|де|та|те|ның|нің)\b', f'из {city}', text, flags=re.I)
            text = re.sub(rf'\b{re.escape(name)}\b', city, text, flags=re.I)
    for canonical, labels in sorted(SKILL_LABELS.items(), key=lambda item: -max(map(len, item[1]))):
        for label in labels:
            text = re.sub(rf'\b{re.escape(label)}\b', canonical, text, flags=re.I)
    for source, target in {'өнеркәсіптік автоматтандыру': 'Промышленная автоматизация', 'киберқауіпсіздік': 'Кибербезопасность', 'білім беру': 'Образование', 'өндіріс': 'Производство', 'сапа және сертификаттау': 'Качество и сертификация', 'инженерия': 'Инженерия'}.items():
        text = re.sub(rf'\b{source}\b', target, text, flags=re.I)
    text = re.sub(r'\b(?:from\s+|between\s+)?(\d{1,2})\s*(?:to|and|[-–—])\s*(\d{1,2})\s*years?(?:\s+of\s+experience)?\b', r'от \1 до \2 лет', text, flags=re.I)
    text = re.sub(r'(\d{1,2})\s*жылдан\s*(\d{1,2})\s*жылға\s*дейін', r'от \1 до \2 лет', text, flags=re.I)
    text = re.sub(r'(\d{1,2})\s*[-–—]\s*(\d{1,2})\s*жыл', r'от \1 до \2 лет', text, flags=re.I)
    replacements = [
        (r'not\s+(?:from|in)', 'не из'), (r'without|excluding|except', 'без'),
        (r'(?:no|not)\s+more\s+than|at\s+most|up\s+to|maximum', 'не более'),
        (r'no\s+less\s+than|at\s+least|minimum', 'не менее'), (r'more\s+than|over', 'более'),
        (r'less\s+than|under', 'менее'), (r'ең\s+көбі|ең\s+көп', 'не более'),
        (r'кемінде|ең\s+азы', 'не менее'),
        (r'еңбек\s+өтілі|жұмыс\s+тәжірибесі|experience', 'опыт'),
        (r'сарапшыларды|сарапшылар|сарапшы|мамандарды|мамандар|маман', 'специалист'),
        (r'керек|қажет', 'нужен'), (r'бойынша', 'по'),
        (r'ізде|тауып\s+бер|табу', 'найди'), (r'and', 'и'), (r'or', 'или'), (r'from', 'из'), (r'in', 'в'), (r'және', 'и'), (r'немесе', 'или'),
    ]
    for pattern, replacement in replacements:
        text = re.sub(rf'\b(?:{pattern})\b', replacement, text, flags=re.I)
    text = re.sub(r'(\d{1,2})\s*жылдан\s*(?:аспайтын|аспайды|артық\s+емес)', r'не более \1 лет', text, flags=re.I)
    text = re.sub(r'(\d{1,2})\s*жылдан\s*кем\s+емес', r'не менее \1 лет', text, flags=re.I)
    text = re.sub(r'\b(PLC|SCADA|GMP|GCP|Python|NLP)\s+жоқ\b', r'без \1', text, flags=re.I)
    text = re.sub(r'\b(\w+(?:\s+\w+)?)\s+емес\b', r'без \1', text, flags=re.I)
    text = re.sub(r'\b(PLC|SCADA|GMP|GCP|Python|NLP)(?:-?сыз|-?сіз)\b', r'без \1', text, flags=re.I)
    text = re.sub(r'\b(?:жыл|жылға|жылдан)\b', 'лет', text, flags=re.I)
    text = re.sub(r'\bдейін\b', '', text, flags=re.I)
    return text
