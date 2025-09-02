from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminRole(BasePermission):
    """
    Custom permission to only allow users with the 'admin' role.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'admin')

class IsAssessorRole(BasePermission):
    """
    Custom permission to only allow users with the 'assessor' role.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'assessor')

class IsHRRole(BasePermission):
    """
    Custom permission to only allow users with the 'hr' role.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'hr')

class IsAdminOrReadOnly(BasePermission):
    """
    Allows full access to admin users, but read-only access to others.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_authenticated and request.user.role == 'admin')

class IsAdminOrAssessor(BasePermission):
    """
    Allows full access to Admin or Assessor roles.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.role == 'admin' or request.user.role == 'assessor'))
