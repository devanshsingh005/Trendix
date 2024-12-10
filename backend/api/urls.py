from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, scrape_products, compare_products, scrape_callback, fetch_products
from . import views
router = DefaultRouter()
router.register(r'products', ProductViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('scrape/', scrape_products, name='scrape-products'),
    path('compare/', compare_products, name='compare-products'),
    path('webhook/scrape-callback/', scrape_callback, name='scrape-callback'),
    path('products/', fetch_products, name='fetch_products'),

]
