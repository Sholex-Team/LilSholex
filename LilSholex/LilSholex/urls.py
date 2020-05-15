from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('groupguard/', include('groupguard.urls')),
    path('support/', include('support.urls')),
    path('persianmeme/', include('persianmeme.urls')),
    path('anonymous/', include('anonymous.urls'))
]
