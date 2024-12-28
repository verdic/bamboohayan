from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('print_place_population/', views.print_place_population, name='print-place-population'),
    path('generate_municipality_chart/', views.generate_municipality_chart, name='generate-municipality-chart'),
    path('heatmap/', views.heatmap_view, name='bamboo-heatmap'),
]