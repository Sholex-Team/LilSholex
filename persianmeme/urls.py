from django.urls import path
from . import views

app_name = 'persianmeme'
urlpatterns = (path('', views.webhook_wrapper),)
