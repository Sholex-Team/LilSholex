from django.urls import path
from persianmeme import views
from django.conf import settings
app_name = 'persianmeme'
urlpatterns = (path(settings.MEME + '/', views.webhook_wrapper),)
