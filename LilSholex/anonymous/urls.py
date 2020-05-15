from django.urls import path
from django.conf import settings
from anonymous import views
app_name = 'anonymous'
urlpatterns = (path(settings.ANONYMOUS + '/', views.webhook),)
