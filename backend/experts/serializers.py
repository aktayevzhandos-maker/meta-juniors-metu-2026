from rest_framework import serializers
from .models import Expert
from .search.engine import parse_query
from .search.taxonomy import INDUSTRIES

class ExpertSerializer(serializers.ModelSerializer):
    availability_label = serializers.CharField(source='get_availability_display', read_only=True)

    class Meta:
        model = Expert
        fields = ['id', 'full_name', 'title', 'industry', 'city', 'skills', 'languages', 'years_experience',
                  'availability', 'availability_label', 'bio', 'is_synthetic']

class SearchRequestSerializer(serializers.Serializer):
    query = serializers.CharField(min_length=3, max_length=1000, trim_whitespace=True)
    limit = serializers.IntegerField(min_value=3, max_value=20, default=3)
    industry = serializers.ChoiceField(choices=list(INDUSTRIES), required=False, allow_null=True)

    city = serializers.CharField(max_length=80, required=False, allow_null=True, trim_whitespace=True)

    min_years_experience = serializers.IntegerField(min_value=0, max_value=60, required=False, allow_null=True)
    max_years_experience = serializers.IntegerField(min_value=0, max_value=60, required=False, allow_null=True)

    def validate(self, values):
        parsed = parse_query(values['query'])
        city, industry = values.get('city'), values.get('industry')
        if city and (city in parsed.excluded_cities or (parsed.cities and city not in parsed.cities)):
            raise serializers.ValidationError({'city': [f'Противоречие: выбран город {city}, но текст задаёт другое условие города. Измените фильтр или запрос.']})
        if industry and (industry in parsed.excluded_industries or (parsed.industries and industry not in parsed.industries)):
            raise serializers.ValidationError({'industry': ['Противоречие между отраслью в фильтре и в тексте запроса.']})
        lower_values = [value for value in [parsed.min_years, values.get('min_years_experience')] if value is not None]
        upper_values = [value for value in [parsed.max_years, values.get('max_years_experience')] if value is not None]
        if parsed.errors or (lower_values and upper_values and max(lower_values) > min(upper_values)):
            raise serializers.ValidationError({'experience': ['Противоречие в диапазоне стажа: «от» больше «до» или фильтр несовместим с текстом.']})
        useful = bool(parsed.skills or parsed.cities or parsed.industries or parsed.excluded_skills or parsed.excluded_cities or parsed.excluded_industries or lower_values or upper_values or city or industry)
        if not useful and not parsed.unrecognized_terms:
            raise serializers.ValidationError({'query': ['Уточните компетенции, город, отрасль или диапазон стажа. Одного слова «специалист» недостаточно.']})
        return values

    def validate_query(self, value):
        if not any(character.isalpha() for character in value):
            raise serializers.ValidationError('Введите запрос с буквами, например «GMP в Алматы».')
        return value
