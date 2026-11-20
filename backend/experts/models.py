from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

class Expert(models.Model):
    class Availability(models.TextChoices):
        AVAILABLE = 'available', 'Доступен'
        LIMITED = 'limited', 'Ограниченно доступен'
        BUSY = 'busy', 'Занят'

    id = models.CharField(primary_key=True, max_length=32)
    full_name = models.CharField(max_length=160)
    title = models.CharField(max_length=200)
    industry = models.CharField(max_length=100, db_index=True)
    city = models.CharField(max_length=80, db_index=True)
    skills = models.JSONField(default=list)
    languages = models.JSONField(default=list)
    years_experience = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(60)])
    availability = models.CharField(max_length=12, choices=Availability.choices, default=Availability.AVAILABLE)
    bio = models.TextField()
    is_synthetic = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.id}: {self.full_name}'

class SearchTotals(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1)
    request_count = models.PositiveBigIntegerField(default=0)
    started_at = models.DateTimeField(null=True)
    last_request_at = models.DateTimeField(null=True)


class SkillDemand(models.Model):
    skill = models.CharField(primary_key=True, max_length=100)
    request_count = models.PositiveBigIntegerField(default=0)
