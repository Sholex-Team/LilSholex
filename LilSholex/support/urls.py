from django.urls import path
from django.conf import settings
from support import views
app_name = 'support'
urlpatterns = [path(settings.SUPPORT + '/', views.webhook)]
