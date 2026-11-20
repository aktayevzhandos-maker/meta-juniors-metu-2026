from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('experts', '0001_initial')]
    operations = [
        migrations.CreateModel(name='SearchTotals', fields=[
            ('id', models.PositiveSmallIntegerField(primary_key=True, default=1, serialize=False)),
            ('request_count', models.PositiveBigIntegerField(default=0)),
            ('started_at', models.DateTimeField(null=True)),
            ('last_request_at', models.DateTimeField(null=True)),
        ]),
        migrations.CreateModel(name='SkillDemand', fields=[
            ('skill', models.CharField(primary_key=True, max_length=100, serialize=False)),
            ('request_count', models.PositiveBigIntegerField(default=0)),
        ]),
    ]
