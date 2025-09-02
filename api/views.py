from rest_framework import viewsets, permissions
from .models import User, Intern, Ticket, Session, AuditLog, Question, SessionAnswer
from .serializers import (
    UserSerializer,
    InternSerializer,
    TicketSerializer,
    SessionSerializer,
    AuditLogSerializer,
)
from .permissions import IsAdminRole, IsAssessorRole, IsAdminOrAssessor

def log_action(user, instance, action_type):
    """Helper function to create an AuditLog entry."""
    AuditLog.objects.create(
        user=user,
        action=f"{action_type}: {instance.__class__.__name__} '{str(instance)}'",
        details=f"ID: {instance.pk}"
    )

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only endpoint for users. Only Admins can access."""
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]

class InternViewSet(viewsets.ModelViewSet):
    """Endpoint for interns."""
    queryset = Intern.objects.all().order_by('full_name')
    serializer_class = InternSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [permissions.IsAuthenticated]
        else:
            self.permission_classes = [IsAdminOrAssessor]
        return super().get_permissions()

    def perform_create(self, serializer):
        instance = serializer.save()
        log_action(self.request.user, instance, "Created")

    def perform_update(self, serializer):
        instance = serializer.save()
        log_action(self.request.user, instance, "Updated")

    def perform_destroy(self, instance):
        log_action(self.request.user, instance, "Deleted")
        instance.delete()

class TicketViewSet(viewsets.ModelViewSet):
    """Endpoint for tickets."""
    queryset = Ticket.objects.all().order_by('title')
    serializer_class = TicketSerializer
    permission_classes = [IsAdminOrAssessor]

    def perform_create(self, serializer):
        instance = serializer.save()
        log_action(self.request.user, instance, "Created")

    def perform_update(self, serializer):
        instance = serializer.save()
        log_action(self.request.user, instance, "Updated")

    def perform_destroy(self, instance):
        log_action(self.request.user, instance, "Deleted")
        instance.delete()

class SessionViewSet(viewsets.ModelViewSet):
    """Endpoint for attestation sessions."""
    queryset = Session.objects.all().order_by('-session_date')
    serializer_class = SessionSerializer

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [IsAssessorRole]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminRole]
        else:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Create a Session and pre-populate its answers."""
        session = serializer.save()
        questions = Question.objects.filter(ticket=session.ticket)
        answers = [
            SessionAnswer(session=session, question=question) for question in questions
        ]
        SessionAnswer.objects.bulk_create(answers)
        session.max_score = questions.count()
        session.save()
        log_action(self.request.user, session, "Created")

    def perform_update(self, serializer):
        instance = serializer.save()
        log_action(self.request.user, instance, "Updated")

    def perform_destroy(self, instance):
        log_action(self.request.user, instance, "Deleted")
        instance.delete()


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only endpoint for audit logs. Only Admins can access."""
    queryset = AuditLog.objects.all().order_by('-timestamp')
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminRole]
