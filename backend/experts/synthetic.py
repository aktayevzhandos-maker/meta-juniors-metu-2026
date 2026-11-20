"""Deterministic fictional registry; no scraped names, contacts or personal data."""
import csv
import random
from pathlib import Path

from .importer import CSV_FIELDS

GROUPS = [
    ('Фармацевтика', 'Эксперт фармацевтической отрасли', [
        ['GMP', 'GCP', 'Клинические исследования', 'Аудит производства'],
        ['GMP', 'Валидация процессов', 'Аудит производства'],
        ['GCP', 'Клинические исследования', 'Фармаконадзор'],
        ['Регистрация лекарств', 'Фармаконадзор', 'GMP'],
        ['GMP', 'Валидация процессов', 'ISO 9001'],
    ]),
    ('Промышленная автоматизация', 'Инженер АСУ ТП', [
        ['PLC', 'SCADA', 'OPC UA'], ['PLC', 'Промышленный IoT', 'Робототехника'],
        ['SCADA', 'OPC UA', 'Безопасность АСУ ТП'],
        ['Предиктивное обслуживание', 'Промышленный IoT', 'Python'],
        ['Робототехника', 'PLC', 'Охрана труда'],
    ]),
    ('Инженерия', 'Инженер-конструктор', [
        ['CAD', 'FEA', 'Метрология'], ['BIM', 'CAD', 'Энергоэффективность'],
        ['Энергоэффективность', 'Возобновляемая энергетика', 'ESG'],
        ['FEA', 'CAD', 'Охрана труда'], ['BIM', 'Энергоэффективность', 'ISO 9001'],
    ]),
    ('IT', 'Инженер программных и интеллектуальных систем', [
        ['Python', 'Машинное обучение', 'NLP'], ['Python', 'Компьютерное зрение', 'MLOps'],
        ['SQL', 'Data Engineering', 'Python'], ['DevOps', 'Kubernetes', 'MLOps'],
        ['React', 'SQL', 'Python'],
    ]),
    ('Кибербезопасность', 'Эксперт по защите информационных систем', [
        ['Пентест', 'Безопасность сетей', 'ISO 27001'], ['SOC', 'Безопасность сетей', 'Python'],
        ['ISO 27001', 'Безопасность сетей', 'Охрана труда'],
        ['Безопасность АСУ ТП', 'SOC', 'OPC UA'], ['Пентест', 'SOC', 'Безопасность АСУ ТП'],
    ]),
    ('Образование', 'Методист цифрового обучения', [
        ['LMS', 'Instructional Design', 'Learning Analytics'],
        ['STEM', 'Робототехника', 'Instructional Design'],
        ['Learning Analytics', 'Python', 'Машинное обучение'],
        ['LMS', 'Instructional Design', 'Охрана труда'], ['STEM', 'CAD', 'LMS'],
    ]),
    ('Производство', 'Консультант производственных процессов', [
        ['Lean', 'Six Sigma', 'ISO 9001'], ['HACCP', 'ISO 9001', 'Аудит производства'],
        ['Охрана труда', 'Робототехника', 'Метрология'],
        ['Предиктивное обслуживание', 'Lean', 'Промышленный IoT'],
        ['ESG', 'Энергоэффективность', 'Охрана труда'],
    ]),
    ('Качество и сертификация', 'Аудитор систем качества', [
        ['ISO 9001', 'Сертификация ЕАЭС', 'Метрология'],
        ['HACCP', 'ISO 9001', 'Аудит производства'],
        ['Метрология', 'Сертификация ЕАЭС', 'Охрана труда'],
        ['ISO 27001', 'ISO 9001', 'Сертификация ЕАЭС'],
        ['GMP', 'ISO 9001', 'Валидация процессов'],
    ]),
]

def generate_rows(seed=2026):
    rng = random.Random(seed)
    cities = ['Алматы', 'Астана', 'Караганда', 'Шымкент', 'Атырау', 'Павлодар']
    contexts = ['консультирование проектных команд', 'анализ и улучшение процессов',
                'внедрение и проверка решений', 'обучение специалистов', 'экспертная оценка проектов']
    rows = []
    for group_index, (industry, title, recipes) in enumerate(GROUPS):
        for offset in range(15):
            number = len(rows) + 1
            skills = recipes[offset % len(recipes)]
            availability = 'available' if offset % 5 == 0 else rng.choice(['available', 'available', 'limited', 'busy'])
            rows.append({
                'id': f'EXP-{number:03d}', 'full_name': f'Синтетический эксперт {number:03d}',
                'title': title, 'industry': industry, 'city': cities[(offset + group_index) % len(cities)],
                'skills': '|'.join(skills), 'languages': 'Русский|Казахский' if number % 3 else 'Русский|Английский',
                'years_experience': 8 + offset % 15, 'availability': availability,
                'bio': f'Вымышленный профиль для тестирования. Направление: {industry}. '
                       f'Задачи: {contexts[offset % len(contexts)]}. Компетенции: {", ".join(skills)}.',
                'is_synthetic': 'true',
            })
    return rows

def write_registry(path, seed=2026):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = generate_rows(seed)
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)
