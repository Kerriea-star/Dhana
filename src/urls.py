from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.documentation import include_docs_urls


API_TITLE = "Dhana"
API_DESCRIPTION = "A Dhana E-shoe Shop API."


urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/v1/", include("api.urls")),
    path('api/v1/docs/', include_docs_urls(title=API_TITLE,
                                           description=API_DESCRIPTION
                                           )),
    path("accounts/", include("accounts.urls")),
    path("", include("shop.urls"))

]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
