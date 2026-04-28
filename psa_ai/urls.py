from django.urls import path

from . import views

app_name = 'psa_ai'

urlpatterns = [
    path('generate-reply/<str:ticket_number>/', views.generate_reply, name='generate_reply'),
    path('suggestion/<int:pk>/', views.suggestion_detail, name='suggestion_detail'),
    path('suggestion/<int:pk>/reject/', views.suggestion_reject, name='suggestion_reject'),
]
