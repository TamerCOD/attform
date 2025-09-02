import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):
    """
    Custom user model with roles.
    """
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('assessor', 'Assessor'),
        ('hr', 'HR'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='assessor')

class Intern(models.Model):
    """
    Represents an intern (Стажёр).
    """
    STATUS_CHOICES = (
        ('active', 'Активен'),
        ('archived', 'Архивирован'),
    )

    LANGUAGE_CHOICES = (
        ('ru', 'RU'),
        ('kg', 'KG'),
        ('en', 'EN'),
        ('uz', 'UZ'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=255, verbose_name="ФИО")
    group = models.CharField(max_length=100, verbose_name="Группа")
    stream = models.CharField(max_length=100, verbose_name="Поток")
    service_languages = models.JSONField(default=list, verbose_name="Языки обслуживания")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата изменения")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', verbose_name="Статус")

    def __str__(self):
        return self.full_name

class Ticket(models.Model):
    """
    Represents a ticket for attestation (Билет).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, verbose_name="Название билета")
    version = models.CharField(max_length=50, verbose_name="Версия")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата изменения")

    def __str__(self):
        return f"{self.title} (v{self.version})"

class Question(models.Model):
    """
    Represents a single question within a ticket.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, related_name='questions', on_delete=models.CASCADE, verbose_name="Билет")
    text = models.TextField(verbose_name="Текст вопроса")

    def __str__(self):
        return self.text[:50]

class Session(models.Model):
    """
    Represents an attestation session (Аттестация).
    """
    STATUS_CHOICES = (
        ('scheduled', 'Запланирована'),
        ('in_progress', 'В процессе'),
        ('completed', 'Проведена'),
        ('cancelled', 'Отменена'),
    )

    RESULT_CHOICES = (
        ('passed', 'Сдано'),
        ('failed', 'Не сдано'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    intern = models.ForeignKey(Intern, on_delete=models.CASCADE, verbose_name="Стажёр")
    ticket = models.ForeignKey(Ticket, on_delete=models.PROTECT, verbose_name="Билет")
    session_date = models.DateTimeField(verbose_name="Дата проведения")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name="Статус сессии")
    result = models.CharField(max_length=10, choices=RESULT_CHOICES, blank=True, null=True, verbose_name="Результат")
    score = models.PositiveIntegerField(default=0, verbose_name="Баллы")
    max_score = models.PositiveIntegerField(default=0, verbose_name="Макс. баллы")

    @property
    def percentage(self):
        if self.max_score > 0:
            return round((self.score / self.max_score) * 100, 2)
        return 0

    def __str__(self):
        return f"Аттестация {self.intern.full_name} от {self.session_date.strftime('%Y-%m-%d')}"

class SessionAnswer(models.Model):
    """
    Stores the result for a specific question within a session.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(Session, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    is_correct = models.BooleanField(default=False, verbose_name="Ответ верный")
    comment = models.TextField(blank=True, verbose_name="Комментарий")

    class Meta:
        unique_together = ('session', 'question')

class AuditLog(models.Model):
    """
    Logs all CUD actions in the system (Журнал аудита).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255, verbose_name="Действие")
    details = models.TextField(blank=True, verbose_name="Детали")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время")

    def __str__(self):
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M')} - {self.action}"
