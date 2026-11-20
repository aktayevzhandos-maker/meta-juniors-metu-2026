from rest_framework import serializers
from .models import Expert
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

    def validate_query(self, value):
        if not any(character.isalpha() for character in value):
            raise serializers.ValidationError('Введите запрос с буквами, например «GMP в Алматы».')
        return value
