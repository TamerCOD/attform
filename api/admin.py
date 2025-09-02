from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User,
    Intern,
    Ticket,
    Question,
    Session,
    SessionAnswer,
    AuditLog,
)

# --- Custom Admin Configurations ---

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin view for Users to include the 'role' field."""
    # Add 'role' to the fieldsets for the user detail page
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Profile', {'fields': ('role',)}),
    )
    # Add 'role' to the add user form
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Custom Profile', {'fields': ('role',)}),
    )
    # Add 'role' to the list display
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = BaseUserAdmin.list_filter + ('role',)
    search_fields = ('username', 'first_name', 'last_name', 'email')

class QuestionInline(admin.TabularInline):
    """Allows editing Questions directly within the Ticket admin page."""
    model = Question
    extra = 1  # Show 1 extra empty form for adding new questions
    ordering = ('id',)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """Admin view for Tickets, with inline Question editing."""
    inlines = [QuestionInline]
    list_display = ('title', 'version', 'created_at', 'updated_at')
    search_fields = ['title', 'version']

@admin.register(Intern)
class InternAdmin(admin.ModelAdmin):
    """Admin view for Interns with convenient filters and search."""
    list_display = ('full_name', 'group', 'stream', 'status', 'created_at')
    list_filter = ('status', 'group', 'stream')
    search_fields = ('full_name', 'group', 'stream')
    ordering = ('-created_at',)

class SessionAnswerInline(admin.TabularInline):
    """
    Shows individual question results within the Session admin page.
    This should be mostly read-only as answers are generated.
    """
    model = SessionAnswer
    extra = 0  # Don't allow adding answers from here directly
    readonly_fields = ('question', 'is_correct', 'comment') # View results, don't edit
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    """Admin view for attestation Sessions."""
    list_display = ('intern', 'ticket', 'session_date', 'status', 'result', 'percentage')
    list_filter = ('status', 'result', 'session_date', 'intern__group', 'intern__stream')
    search_fields = ('intern__full_name', 'ticket__title')
    readonly_fields = ('percentage', 'score', 'max_score')
    ordering = ('-session_date',)
    # inlines = [SessionAnswerInline] # This could be added later if needed for review

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """A read-only admin view for the Audit Log."""
    list_display = ('timestamp', 'user', 'action')
    list_filter = ('user', 'timestamp')
    search_fields = ('action', 'details', 'user__username')
    ordering = ('-timestamp',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

# Note: Question and SessionAnswer are managed via inlines,
# so they don't need to be registered separately.
