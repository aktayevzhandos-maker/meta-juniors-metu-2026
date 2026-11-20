"""One-process local demo startup; retain imported/edited data on later restarts."""
import os
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.core.management import call_command, execute_from_command_line
from experts.models import Expert

if __name__ == '__main__':
    call_command('migrate', interactive=False)
    if not Expert.objects.exists():
        call_command('import_experts', str(Path(__file__).resolve().parent.parent / 'data' / 'experts.csv'))
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000', '--noreload'])
