from rest_framework import serializers
from .models import InterviewQuestion, InterviewSession


class InterviewQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewQuestion
        fields = [
            'id',
            'order',
            'category',
            'question_text',
            'intent_explanation',
            'sample_approach',
            'user_answer',
            'score',
            'feedback_summary',
            'strengths',
            'areas_for_improvement',
            'ideal_points',
            'evaluated_at',
        ]


class InterviewSessionSerializer(serializers.ModelSerializer):
    questions = InterviewQuestionSerializer(many=True, read_only=True)
    answered_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = InterviewSession
        fields = [
            'id',
            'target_role',
            'difficulty',
            'question_type',
            'total_questions',
            'overall_score',
            'is_completed',
            'created_at',
            'completed_at',
            'answered_count',
            'questions',
        ]


class InterviewStartRequestSerializer(serializers.Serializer):
    target_role = serializers.CharField(required=False, allow_blank=True, max_length=200)
    difficulty = serializers.ChoiceField(choices=['junior', 'mid', 'senior'], default='junior')
    question_type = serializers.ChoiceField(choices=['mixed', 'technical', 'hr'], default='mixed')
    count = serializers.IntegerField(min_value=1, max_value=5, default=3)


class InterviewAnswerSubmitSerializer(serializers.Serializer):
    answer = serializers.CharField(min_length=10, max_length=5000)
