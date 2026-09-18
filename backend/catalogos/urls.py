from rest_framework.routers import DefaultRouter

from .views import CategoriaViewSet, EntidadViewSet, RegionViewSet

router = DefaultRouter()
router.register("regiones", RegionViewSet, basename="region")
router.register("entidades", EntidadViewSet, basename="entidad")
router.register("categorias", CategoriaViewSet, basename="categoria")

urlpatterns = router.urls
