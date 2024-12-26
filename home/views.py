from django.shortcuts import render
from bamboo_species.models import BambooSpecies, SpeciesLocation
from django.db.models import Count, Sum, Value
from django.db.models.functions import Concat
import random
from django.http import JsonResponse

import plotly.graph_objects as go
from plotly.offline import plot


def get_all_habitats():
   habitats = BambooSpecies.objects.annotate(habitat_concat=Concat('habitat', Value(','))).values_list('habitat_concat', flat=True).distinct()
   habitats = [habitat[:-1].split(',') for habitat in habitats]
   habitats = tuple(set([item.strip() for sublist in habitats for item in sublist]))
   return habitats

def get_maped_species():
    return SpeciesLocation.objects.values('bamboo_species').annotate(location_count=Count('bamboo_species')).filter(location_count__gt=0).count()

def get_population_all():
   total_area_population = SpeciesLocation.objects.aggregate(total_population=Sum('area_population'))
   sum_area_population = 0
   if total_area_population['total_population']:
      sum_area_population = total_area_population['total_population']
   return sum_area_population

def generate_column_chart(data):
   color_list = [f'rgb({random.randint(0, 255)}, {random.randint(0, 255)}, {random.randint(0, 255)})' for _ in range(len(data))]
   
   fig = go.Figure(data=[go.Bar(x=list(data.keys()), y=list(data.values()), marker=dict(color=color_list))])
   chart_html = plot(fig, output_type='div')
   return chart_html

def get_chart_data():
   species_population = SpeciesLocation.objects.values('bamboo_species__common_name').annotate(sum_population=Sum('area_population'))

   # Prepare the data for the column chart
   data = {}
   for entry in species_population:
      bamboo_species = entry['bamboo_species__common_name']
      sum_population = entry['sum_population']
      data[bamboo_species] = sum_population
   return data

def generate_place_population_report():
   bamboo_species = BambooSpecies.objects.all()
   report_data = []

   for species in bamboo_species:
      locations = SpeciesLocation.objects.filter(bamboo_species=species)
      for location in locations:
         report_data.append({
               'common_name': species.common_name,
               'place': location.place,
               'area_population': location.area_population
         })

   return report_data
    
def index(request):
   context = {
        'column_chart': generate_column_chart(get_chart_data()),
        'species': BambooSpecies.objects.all().count(),
        'mapped_species': get_maped_species(),
        'area_population_all': get_population_all(),
        'report_data': generate_place_population_report(),
        'municipalities': [
            "Abulug", "Alcala", "Allacapan", "Amulung", "Aparri", "Baggao", "Ballesteros", "Buguey", "Calayan",
            "Camalaniugan", "Claveria", "Enrile", "Gattaran", "Gonzaga", "Iguig", "Lal-lo", "Lasam", "Pamplona",
            "Peñablanca", "Piat", "Rizal", "Sanchez-Mira", "Santa Ana", "Santa Praxedes", "Santa Teresita", 
            "Santo Niño", "Solana", "Tuao", "Tuguegarao City"
        ]
    }
   
   return render(request, 'home.html', context) 

def generate_municipality_chart(request):
    municipalities = [
        "Abulug", "Alcala", "Allacapan", "Amulung", "Aparri", "Baggao", "Ballesteros", "Buguey", "Calayan",
        "Camalaniugan", "Claveria", "Enrile", "Gattaran", "Gonzaga", "Iguig", "Lal-lo", "Lasam", "Pamplona",
        "Peñablanca", "Piat", "Rizal", "Sanchez-Mira", "Santa Ana", "Santa Praxedes", "Santa Teresita", 
        "Santo Niño", "Solana", "Tuao", "Tuguegarao City"
    ]
    selected_municipality = request.GET.get('municipality', None)
    
    if selected_municipality:
        species_data = SpeciesLocation.objects.filter(
            place__icontains=selected_municipality
        ).values('bamboo_species__common_name').annotate(species_count=Count('bamboo_species')).order_by('-species_count')

        if not species_data.exists():
            return JsonResponse({'error': f"No bamboo species recorded yet in {selected_municipality}"}, status=404)
        
        data = {entry['bamboo_species__common_name']: entry['species_count'] for entry in species_data}
    else:
        species_data = SpeciesLocation.objects.values(
            'place'
        ).annotate(species_count=Count('bamboo_species')).order_by('-species_count')
        data = {entry['place']: entry['species_count'] for entry in species_data}

    chart_html = generate_column_chart(data)
    return JsonResponse({'chart_html': chart_html})

from django.template.loader import render_to_string
# from django.http import HttpResponse

def print_place_population(request):
   # Generate the HTML content using the template and data
   report_data = generate_place_population_report()
   context = {'report_data': report_data}
   
   return render(request, 'reports/print_place_population_report.html', context)
