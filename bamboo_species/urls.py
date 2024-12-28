from django.urls import path
from . import views

urlpatterns = [
    path('', views.species_list, name='species-list'),
    path('<int:species_id>', views.species_detail, name='species-detail'),
    path('update/<int:species_id>', views.species_update, name='species-update'),
    path('create/', views.species_create, name='species-create'),
    path('delete/<int:species_id>', views.species_delete, name='species-delete'),
    path('morpho_list/', views.morpho_list, name='morpho-list'),
    path('morpho_create/<int:species_id>', views.morpho_create, name='morpho-create'),
    path('morpho_update/<int:pk>', views.morpho_update, name='morpho-update'),
    path('morpho_delete/<int:pk>', views.morpho_delete, name='morpho-delete'),
    path('phytochem_create/<int:species_id>', views.phytochem_create, name='phytochem-create'),
    path('phytochem_update/<int:pk>', views.phytochem_update, name='phytochem-update'),
    path('phytochem_delete/<int:pk>', views.phytochem_delete, name='phytochem-delete'),
    path('molecular_create/<int:species_id>', views.molecular_create, name='molecular-create'),
    path('molecular_update/<int:pk>', views.molecular_update, name='molecular-update'),
    path('molecular_delete/<int:pk>', views.molecular_delete, name='molecular-delete'),
    path('coord_list/', views.coord_list, name='coord-list'),
    path('coord_list/<int:species_id>/', views.coord_list, name='coord-list-species'),
    path('species/coord_list/<int:species_id>/', views.coord_list, name='species-coord-list'),
    path('upload_coord_data/<int:species_id>/', views.upload_coord_data, name='upload-coord-data'),
    # path('species/coord_list_species/<int:species_id>/', views.coord_list_species, name='species-coord-list'),
    path('coord_species_create/<int:species_id>', views.coord_species_create, name='coord-species-create'),
    path('coord_create/', views.coord_create, name='coord-create'),
    path('coord_detail/<str:pk>', views.coord_detail, name='coord-detail'),
    path('coord_update/<str:pk>', views.coord_update, name='coord-update'),
    path('coord_delete/<str:pk>', views.coord_delete, name='coord-delete'),

]