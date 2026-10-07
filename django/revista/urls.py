from django.urls import path
from . import views

urlpatterns = [
    path("", views.ola, name="ola")
]