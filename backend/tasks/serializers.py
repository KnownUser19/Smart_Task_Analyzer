"""
Serializers for Task API

Handles validation and serialization of task data for API endpoints.
"""
from rest_framework import serializers


class TaskInputSerializer(serializers.Serializer):
    """Serializer for incoming task data."""
    
    id = serializers.CharField(required=False, allow_null=True)
    title = serializers.CharField(max_length=255, required=True)
    due_date = serializers.DateField(required=False, allow_null=True)
    estimated_hours = serializers.FloatField(
        required=False,
        default=1.0,
        min_value=0.1
    )
    importance = serializers.IntegerField(
        required=False,
        default=5,
        min_value=1,
        max_value=10
    )
    dependencies = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    
    def validate_title(self, value):
        """Ensure title is not empty or whitespace only."""
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip()


class TaskListInputSerializer(serializers.Serializer):
    """Serializer for a list of tasks."""
    
    tasks = TaskInputSerializer(many=True)
    strategy = serializers.ChoiceField(
        choices=[
            ('smart_balance', 'Smart Balance'),
            ('fastest_wins', 'Fastest Wins'),
            ('high_impact', 'High Impact'),
            ('deadline_driven', 'Deadline Driven')
        ],
        required=False,
        default='smart_balance'
    )
    custom_weights = serializers.DictField(
        required=False,
        allow_null=True
    )


class ScoringBreakdownSerializer(serializers.Serializer):
    """Serializer for individual score breakdown."""
    
    score = serializers.FloatField()
    weight = serializers.FloatField()
    weighted_score = serializers.FloatField()
    explanation = serializers.CharField()


class TaskOutputSerializer(serializers.Serializer):
    """Serializer for scored task output."""
    
    id = serializers.CharField(required=False)
    title = serializers.CharField()
    due_date = serializers.CharField(allow_null=True)
    estimated_hours = serializers.FloatField()
    importance = serializers.IntegerField()
    dependencies = serializers.ListField(child=serializers.CharField())
    priority_score = serializers.FloatField()
    priority_level = serializers.CharField()
    scoring_breakdown = serializers.DictField()
    strategy_used = serializers.CharField()
    warnings = serializers.ListField(child=serializers.CharField())


class AnalysisResultSerializer(serializers.Serializer):
    """Serializer for complete analysis result."""
    
    tasks = TaskOutputSerializer(many=True)
    total_count = serializers.IntegerField()
    strategy = serializers.CharField()
    weights = serializers.DictField()
    circular_dependencies = serializers.ListField()
    analysis_date = serializers.CharField()
    priority_distribution = serializers.DictField()


class SuggestionItemSerializer(serializers.Serializer):
    """Serializer for a single suggestion."""
    
    rank = serializers.IntegerField()
    task = TaskOutputSerializer()
    recommendation_reason = serializers.CharField()
    actionable_insight = serializers.CharField()


class SuggestionsResultSerializer(serializers.Serializer):
    """Serializer for suggestions result."""
    
    suggestions = SuggestionItemSerializer(many=True)
    strategy = serializers.CharField()
    analysis_date = serializers.CharField()
    total_tasks_analyzed = serializers.IntegerField()
