from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('print_place_population/', views.print_place_population, name='print-place-population'),
    path('generate_municipality_chart/', views.generate_municipality_chart, name='generate-municipality-chart'),
    path('heatmap/', views.heatmap_view, name='bamboo-heatmap'),
    path('habitat-insights/', views.habitat_insights_view, name='habitat-insights'),
    path('uses-insights/', views.uses_insights_view, name='uses-insights'),
    path('morphological-insights/', views.morphological_insights_view, name='morphological-insights'),
    path('phytochemical-insights/', views.phytochemical_insights_view, name='phytochemical-insights'),
    path('molecular-insights/', views.molecular_insights_view, name='molecular-insights'),
    path('propagation-rhizome-insights/', views.propagation_rhizome_insights_view, name='propagation-rhizome-insights'),
    path('population-collection-insights/', views.population_collection_insights_view, name='population-collection-insights'),
]