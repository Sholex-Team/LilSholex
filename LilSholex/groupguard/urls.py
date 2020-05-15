from django.urls import path
from django.conf import settings
from groupguard import views

app_name = 'groupguard'
urlpatterns = [
    path(settings.GROUP + '/', views.webhook),
    path('login/<str:login_token>/', views.login),
    path('panel/', views.panel, name='panel'),
    path('logout/', views.logout, name='logout')
]
