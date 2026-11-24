from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from restaurante.api_views import (
    ComboViewSet,
    ComandaViewSet,
    ItemViewSet,
    MesaViewSet,
    PratoViewSet,
)

router = DefaultRouter()
router.register(r'pratos', PratoViewSet, basename='api-prato')
router.register(r'combos', ComboViewSet, basename='api-combo')
router.register(r'mesas', MesaViewSet, basename='api-mesa')
router.register(r'comandas', ComandaViewSet, basename='api-comanda')
router.register(r'itens', ItemViewSet, basename='api-item')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('', include('restaurante.urls')),
]