from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('nothingspecialbro/', admin.site.urls),
    path('persianmeme/', include('persianmeme.urls'))
]
