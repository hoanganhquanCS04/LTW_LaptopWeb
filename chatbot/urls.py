from django.urls import path
from . import views

urlpatterns = [
    path('ask/', views.ask_chatbot, name='ask_chatbot'),
]