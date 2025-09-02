from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# DefaultRouter automatically creates the URL patterns for our ViewSets.
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'interns', views.InternViewSet, basename='intern')
router.register(r'tickets', views.TicketViewSet, basename='ticket')
router.register(r'sessions', views.SessionViewSet, basename='session')
router.register(r'auditlogs', views.AuditLogViewSet, basename='auditlog')

# The API URLs are now determined automatically by the router.
# The `urlpatterns` will be included in the main project's urls.py
urlpatterns = [
    path('', include(router.urls)),
]
