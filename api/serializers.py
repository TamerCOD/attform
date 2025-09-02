from rest_framework import serializers
from .models import (
    User,
    Intern,
    Ticket,
    Question,
    Session,
    SessionAnswer,
    AuditLog,
)

class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model, exposing basic information."""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role']

class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for the Question model."""
    class Meta:
        model = Question
        fields = ['id', 'text']

class TicketSerializer(serializers.ModelSerializer):
    """
    Serializer for the Ticket model.
    Includes nested questions for read operations. For write operations,
    questions should be managed via a separate endpoint.
    """
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = ['id', 'title', 'version', 'questions', 'created_at', 'updated_at']

class InternSerializer(serializers.ModelSerializer):
    """Serializer for the Intern model."""
    class Meta:
        model = Intern
        fields = '__all__' # Expose all fields for simplicity in the admin-like UI

class SessionAnswerSerializer(serializers.ModelSerializer):
    """Serializer for viewing answers within a session."""
    question = serializers.StringRelatedField()

    class Meta:
        model = SessionAnswer
        fields = ['id', 'question', 'is_correct', 'comment']

class SessionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Session model.
    Handles both read (detailed) and write (ID-based) operations for relationships.
    """
    # Use nested serializers for read operations to provide rich detail
    intern = InternSerializer(read_only=True)
    ticket = TicketSerializer(read_only=True)
    answers = SessionAnswerSerializer(many=True, read_only=True)

    # Use PrimaryKeyRelatedField for write operations to accept IDs
    intern_id = serializers.PrimaryKeyRelatedField(
        queryset=Intern.objects.all(), source='intern', write_only=True, label="Intern ID"
    )
    ticket_id = serializers.PrimaryKeyRelatedField(
        queryset=Ticket.objects.all(), source='ticket', write_only=True, label="Ticket ID"
    )

    class Meta:
        model = Session
        fields = [
            'id', 'intern', 'ticket', 'session_date', 'status', 'result',
            'score', 'max_score', 'percentage', 'answers', 'intern_id', 'ticket_id'
        ]
        # These fields are calculated or managed by the backend logic, not set directly by user
        read_only_fields = ['score', 'max_score', 'percentage', 'answers', 'result']


class AuditLogSerializer(serializers.ModelSerializer):
    """Read-only serializer for the AuditLog."""
    user = serializers.StringRelatedField()

    class Meta:
        model = AuditLog
        fields = ('id', 'user', 'action', 'details', 'timestamp')
        read_only_fields = fields
