from django.urls import path
from . import views

app_name = 'dev'

urlpatterns = [
    path('console/', views.sql_console, name='console'),
]
