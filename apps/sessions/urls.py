from django.urls import path
from . import views

app_name = 'sessions'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('history/', views.session_history, name='history'),
    path('stats/', views.statistics, name='statistics'),
    path('sessions/create/', views.create_session, name='create_session'),
    path('sessions/<int:pk>/start/', views.start_session, name='start_session'),
    path('sessions/<int:pk>/stop/', views.stop_session, name='stop_session'),
    path('sessions/<int:pk>/delete/', views.delete_session, name='delete_session'),
    path('sessions/<int:pk>/timer/', views.session_timer, name='session_timer'),
]
