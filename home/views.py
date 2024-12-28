from django.shortcuts import render
from django.db.models import Count, Sum, Value
from django.db.models.functions import Concat
import random
from django.http import JsonResponse, HttpResponse
from collections import Counter
import re
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.offline import plot
from scipy.cluster.hierarchy import dendrogram, linkage

############## FOR HEATMAP ##############
from folium import Map
from folium.plugins import HeatMap
from bamboo_species.models import MolecularProfile, SpeciesLocation, MorphologicalProfile, PhytochemicalProfile, BambooSpecies, SpeciesLocation
import os
from django.conf import settings

def population_collection_insights_view(request):
    # Fetch data from SpeciesLocation
    locations = SpeciesLocation.objects.all()

    # Define the list of municipalities
    municipalities = [
        "Abulug", "Alcala", "Allacapan", "Amulung", "Aparri", "Baggao", "Ballesteros", "Buguey", "Calayan",
        "Camalaniugan", "Claveria", "Enrile", "Gattaran", "Gonzaga", "Iguig", "Lal-lo", "Lasam", "Pamplona",
        "Peñablanca", "Piat", "Rizal", "Sanchez-Mira", "Santa Ana", "Santa Praxedes", "Santa Teresita",
        "Santo Niño", "Solana", "Tuao", "Tuguegarao City"
    ]

    # Prepare data for Line Chart (Population Over Time)
    dates = []
    populations = []

    for location in locations:
        if location.collection_date:
            dates.append(location.collection_date)
            populations.append(location.area_population)

    # Sort data by date
    data = pd.DataFrame({"date": dates, "population": populations}).sort_values("date")

    # Generate Line Chart
    line_fig = go.Figure()
    line_fig.add_trace(go.Scatter(
        x=data["date"],
        y=data["population"].cumsum(),
        mode="lines+markers",
        line=dict(color="green"),
    ))
    line_fig.update_layout(
        title="Changes in Bamboo Population Over Time",
        xaxis_title="Collection Date",
        yaxis_title="Cumulative Population",
    )
    line_chart_html = plot(line_fig, output_type="div")

    # Match municipalities with SpeciesLocation.place
    municipality_counts = {municipality: 0 for municipality in municipalities}
    for location in locations:
        for municipality in municipalities:
            if municipality.lower() in location.place.lower():
                municipality_counts[municipality] += 1
                break

    # Generate Histogram (Frequency by Municipality)
    hist_municipality_fig = go.Figure(data=[
        go.Bar(x=list(municipality_counts.keys()), y=list(municipality_counts.values()), marker_color="blue")
    ])
    hist_municipality_fig.update_layout(
        title="Frequency of Collections by Municipality",
        xaxis_title="Municipality",
        yaxis_title="Frequency",
    )
    hist_municipality_chart_html = plot(hist_municipality_fig, output_type="div")

    # Generate Histogram (Frequency by Date)
    dates_only = [location.collection_date for location in locations if location.collection_date]
    hist_date_fig = go.Figure(data=[
        go.Histogram(x=dates_only, marker_color="orange")
    ])
    hist_date_fig.update_layout(
        title="Frequency of Collections by Date",
        xaxis_title="Date",
        yaxis_title="Frequency",
    )
    hist_date_chart_html = plot(hist_date_fig, output_type="div")

    # Render the charts in a template
    return render(request, "dss/population_collection_insights.html", {
        "line_chart_html": line_chart_html,
        "hist_municipality_chart_html": hist_municipality_chart_html,
        "hist_date_chart_html": hist_date_chart_html,
    })

def propagation_rhizome_insights_view(request):
    # Fetch data for propagation and rhizome types
    species_data = BambooSpecies.objects.values('propagation', 'rhyzome_type')

    # Prepare data for the Pie Chart (Propagation Methods)
    propagation_methods = [species['propagation'].lower() for species in species_data if species['propagation']]
    propagation_counts = Counter(propagation_methods)

    # Generate Pie Chart
    pie_fig = go.Figure(data=[
        go.Pie(labels=list(propagation_counts.keys()), values=list(propagation_counts.values()))
    ])
    pie_fig.update_layout(title="Popularity of Propagation Methods")
    pie_chart_html = plot(pie_fig, output_type="div")

    # Prepare data for the Bar Chart (Rhizome Types)
    rhizome_types = [species['rhyzome_type'].lower() for species in species_data if species['rhyzome_type']]
    rhizome_counts = Counter(rhizome_types)

    # Generate Bar Chart
    bar_fig = go.Figure(data=[
        go.Bar(x=list(rhizome_counts.keys()), y=list(rhizome_counts.values()))
    ])
    bar_fig.update_layout(
        title="Distribution of Rhizome Types",
        xaxis_title="Rhizome Types",
        yaxis_title="Count",
    )
    bar_chart_html = plot(bar_fig, output_type="div")

    # Render the charts in a template
    return render(request, "dss/propagation_rhizome_insights.html", {
        "pie_chart_html": pie_chart_html,
        "bar_chart_html": bar_chart_html,
    })

def molecular_insights_view(request):
    # Fetch molecular data
    profiles = MolecularProfile.objects.all()

    # Prepare data for Scatter Plot
    species_names = []
    percentage_identifications = []
    for profile in profiles:
        species_names.append(profile.dna_rbcl_species)
        percentage_identifications.append(profile.percentage_identification)

    # Scatter Plot for DNA Identification Percentages
    scatter_fig = go.Figure()
    scatter_fig.add_trace(go.Scatter(
        x=species_names,
        y=percentage_identifications,
        mode="markers",
        marker=dict(size=10, color="blue"),
    ))
    scatter_fig.update_layout(
        title="DNA Identification Percentages vs. Species",
        xaxis_title="Species",
        yaxis_title="Identification Percentage",
    )
    scatter_chart_html = plot(scatter_fig, output_type="div")

    # Prepare data for Tree Diagram (Phylogenetic Relationships)
    # Example using dna_query_length as distances (can be replaced with custom metrics)
    distances = np.array([profile.dna_query_length for profile in profiles]).reshape(-1, 1)
    species_labels = [profile.dna_rbcl_species for profile in profiles]
    linked = linkage(distances, method="single")
    
    # Generate Dendrogram
    dendrogram_fig = go.Figure()
    dendrogram_data = dendrogram(linked, labels=species_labels, no_plot=True)
    for i, d in enumerate(dendrogram_data["icoord"]):
        dendrogram_fig.add_trace(go.Scatter(
            x=dendrogram_data["dcoord"][i],
            y=d,
            mode="lines",
            line=dict(color="black"),
        ))
    dendrogram_fig.update_layout(
        title="Phylogenetic Tree Diagram",
        xaxis_title="Species",
        yaxis_title="Distance",
    )
    dendrogram_chart_html = plot(dendrogram_fig, output_type="div")

    # Render the charts in a template
    return render(request, "dss/molecular_insights.html", {
        "scatter_chart_html": scatter_chart_html,
        "dendrogram_chart_html": dendrogram_chart_html,
    })

def phytochemical_insights_view(request):
    # Fetch phytochemical data
    profiles = PhytochemicalProfile.objects.all()

    # Mapping for textual to numeric conversion
    phytochemical_mapping = {
        "absent": 0,
        "slightly present": 1,
        "moderately present": 2,
        "highly present": 3
    }

    # Prepare data for analysis
    species_names = []
    phytochemicals = ["anthocyanin", "flavonoids", "phenols", "tannins"]
    data = {phytochemical: [] for phytochemical in phytochemicals}

    for profile in profiles:
        species_names.append(profile.bamboo_species.common_name)
        
        # Convert textual values to numeric using the mapping
        data["anthocyanin"].append(phytochemical_mapping.get(profile.anthocyanin.lower(), 0))
        data["flavonoids"].append(phytochemical_mapping.get(profile.flavonoids.lower(), 0))
        data["phenols"].append(phytochemical_mapping.get(profile.phenols.lower(), 0))
        data["tannins"].append(phytochemical_mapping.get(profile.tannins.lower(), 0))

    # Heatmap for phytochemical intensities
    heatmap_fig = go.Figure(
        data=go.Heatmap(
            z=[data[phytochemical] for phytochemical in phytochemicals],
            x=species_names,
            y=phytochemicals,
            colorscale="Viridis",
        )
    )
    heatmap_fig.update_layout(
        title="Phytochemical Intensities Across Species",
        xaxis_title="Species",
        yaxis_title="Phytochemicals",
    )
    heatmap_html = plot(heatmap_fig, output_type="div")

    # Bar Chart for high concentrations
    bar_fig = go.Figure()
    for phytochemical in phytochemicals:
        bar_fig.add_trace(
            go.Bar(
                x=species_names,
                y=data[phytochemical],
                name=phytochemical,
            )
        )
    bar_fig.update_layout(
        title="Species with High Phytochemical Concentrations",
        xaxis_title="Species",
        yaxis_title="Concentration",
        barmode="group",
    )
    bar_chart_html = plot(bar_fig, output_type="div")

    # Render the charts in a template
    return render(request, "dss/phytochemical_insights.html", {
        "heatmap_html": heatmap_html,
        "bar_chart_html": bar_chart_html,
    })

def morphological_insights_view(request):
    # Fetch morphological data
    profiles = MorphologicalProfile.objects.all()

    # Prepare data for Boxplots (Internode Length and Width)
    species_names = []
    internode_lengths = []
    internode_widths = []

    for profile in profiles:
        species_names.append(profile.bamboo_species.common_name)
        internode_lengths.append(profile.internode_length)
        internode_widths.append(profile.internode_width)

    # Boxplot for Internode Length
    boxplot_length = go.Figure()
    boxplot_length.add_trace(go.Box(y=internode_lengths, name="Internode Length"))
    boxplot_length.update_layout(
        title="Distribution of Internode Length Across Species",
        yaxis_title="Internode Length (cm)"
    )
    boxplot_length_html = plot(boxplot_length, output_type="div")

    # Boxplot for Internode Width
    boxplot_width = go.Figure()
    boxplot_width.add_trace(go.Box(y=internode_widths, name="Internode Width"))
    boxplot_width.update_layout(
        title="Distribution of Internode Width Across Species",
        yaxis_title="Internode Width (cm)"
    )
    boxplot_width_html = plot(boxplot_width, output_type="div")

    # Prepare data for Radar Chart
    radar_data = []
    radar_categories = ["Internode Length", "Internode Width"]
    for profile in profiles:
        radar_data.append(
            {
                "species": profile.bamboo_species.common_name,
                "values": [profile.internode_length, profile.internode_width],
            }
        )

    # Generate Radar Chart
    radar_fig = go.Figure()
    for data in radar_data:
        radar_fig.add_trace(go.Scatterpolar(
            r=data["values"],
            theta=radar_categories,
            fill="toself",
            name=data["species"]
        ))
    radar_fig.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        title="Comparison of Morphological Attributes Across Species",
    )
    radar_chart_html = plot(radar_fig, output_type="div")

    # Render the template with the charts
    return render(request, "dss/morphological_insights.html", {
        "boxplot_length_html": boxplot_length_html,
        "boxplot_width_html": boxplot_width_html,
        "radar_chart_html": radar_chart_html,
    })

def uses_insights_view(request):
    # Fetch all uses text from BambooSpecies
    species_uses = BambooSpecies.objects.values('common_name', 'uses')

    # Prepare data for charts
    all_uses = []  # For pie chart
    species_uses_data = {}  # For stacked bar chart

    for species in species_uses:
        species_name = species['common_name']
        uses_text = species['uses']
        
        if uses_text:
            # Tokenize uses (split by commas and normalize)
            uses = [use.strip().lower() for use in uses_text.split(',')]
            all_uses.extend(uses)

            # Store the uses for each species
            species_uses_data[species_name] = uses

    # Count the frequency of each use (for pie chart)
    use_counts = Counter(all_uses)

    # Generate a Pie Chart for Proportion of Uses
    pie_fig = go.Figure(data=[
        go.Pie(labels=list(use_counts.keys()), values=list(use_counts.values()))
    ])
    pie_fig.update_layout(title="Proportion of Species by Primary Use")
    pie_chart_html = plot(pie_fig, output_type='div')

    # Prepare data for Stacked Bar Chart
    unique_uses = list(use_counts.keys())
    species_names = list(species_uses_data.keys())
    bar_data = {use: [0] * len(species_names) for use in unique_uses}

    for i, species in enumerate(species_names):
        for use in species_uses_data[species]:
            bar_data[use][i] += 1

    # Generate a Stacked Bar Chart
    bar_fig = go.Figure()
    for use, values in bar_data.items():
        bar_fig.add_trace(go.Bar(
            x=species_names,
            y=values,
            name=use
        ))
    bar_fig.update_layout(
        title="Multiple Uses for Each Species",
        xaxis_title="Bamboo Species",
        yaxis_title="Number of Uses",
        barmode='stack'
    )
    bar_chart_html = plot(bar_fig, output_type='div')

    # Render the charts in a template
    return render(request, "dss/uses_insights.html", {
        "pie_chart_html": pie_chart_html,
        "bar_chart_html": bar_chart_html
    })

def habitat_insights_view(request):
    # Fetch all habitat text from BambooSpecies
    habitats = BambooSpecies.objects.values_list('habitat', flat=True)

    # Tokenize and normalize the text
    tokens = []
    for habitat in habitats:
        if habitat:
            # Remove punctuation, split by spaces, and normalize to lowercase
            words = re.findall(r'\b\w+\b', habitat.lower())
            tokens.extend(words)

    # Count the frequency of each token
    token_counts = Counter(tokens)

    # Filter out insignificant tokens (e.g., very short words, stop words)
    stop_words = {'and', 'or', 'in', 'on', 'of', 'with', 'to', 'a', 'the'}  # Add more as needed
    filtered_tokens = {word: count for word, count in token_counts.items() if word not in stop_words and len(word) > 2}

    # Sort tokens by frequency
    sorted_tokens = dict(sorted(filtered_tokens.items(), key=lambda x: x[1], reverse=True))

    # Generate a bar chart using Plotly
    fig = go.Figure(data=[
        go.Bar(x=list(sorted_tokens.keys()), y=list(sorted_tokens.values()))
    ])
    fig.update_layout(
        title="Habitat Suitability Chart",
        xaxis_title="Habitat Keywords",
        yaxis_title="Frequency",
    )
    chart_html = plot(fig, output_type='div')

    # Render the chart in a template
    return render(request, "dss/habitat_insights.html", {"chart_html": chart_html})

def heatmap_view(request):
    # Extract data from SpeciesLocation model
    locations = SpeciesLocation.objects.all()
    heatmap_data = []
    for location in locations:
        try:
            lat, lon, _ = parse_coordinates_with_elevation(location.coordinate)  # Utility function to parse coordinates
            heatmap_data.append([lat, lon, location.area_population])
        except Exception as e:
            print(f"Error processing location {location}: {e}")

    # Create a folium map centered around a default coordinate
    map_center = [18.16668, 121.74556]  # Example center point
    bamboo_map = Map(location=map_center, zoom_start=10)

    # Add heatmap layer
    HeatMap(heatmap_data, radius=15).add_to(bamboo_map)

    # Ensure the directory exists
    output_dir = os.path.join(settings.BASE_DIR, "static/dss")
    os.makedirs(output_dir, exist_ok=True)

    # Save the map to an HTML file
    map_path = os.path.join(output_dir, "bamboo_heatmap.html")
    bamboo_map.save(map_path)

    # Return the file path as a response (or render it in a template)
    return render(request, "dss/bamboo_heatmap.html", {"heatmap_data": heatmap_data})

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

def parse_coordinates_with_elevation(coordinate):
    try:
        # Remove commas and split the coordinate string
        cleaned_coordinate = coordinate.replace(",", "")
        parts = cleaned_coordinate.split()

        # Extract latitude and longitude
        lat = float(parts[0].replace("°N", "").replace("°S", "-").strip())
        lon = float(parts[1].replace("°E", "").replace("°W", "-").strip())

        # Extract elevation (last part of the string)
        elevation_ft = parts[-1].replace("Ft", "").strip()
        elevation_m = float(elevation_ft) * 0.3048  # Convert feet to meters

        return lat, lon, elevation_m
    except Exception as e:
        print(f"Error parsing coordinate '{coordinate}': {e}")
        return None, None, None

def generate_elevation_chart():
    elevation_data = {}
    species_list = BambooSpecies.objects.values_list('common_name', flat=True)

    for species in species_list:
        locations = SpeciesLocation.objects.filter(bamboo_species__common_name=species)
        elevations = []
        for location in locations:
            _, _, elevation_m = parse_coordinates_with_elevation(location.coordinate)
            if elevation_m is not None:
                elevations.append(elevation_m)

        if elevations:
            elevation_data[species] = {
                "max_elevation": max(elevations),
                "min_elevation": min(elevations),
            }
        else:
            print(f"No valid elevation data for species: {species}")

    # Prepare data for the chart
    species_names = list(elevation_data.keys())
    max_elevations = [elevation_data[species]['max_elevation'] for species in species_names]
    min_elevations = [elevation_data[species]['min_elevation'] for species in species_names]

    # Generate Plotly Chart
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=species_names,
        y=max_elevations,
        name='Max Elevation',
        marker_color='blue'
    ))
    fig.add_trace(go.Bar(
        x=species_names,
        y=min_elevations,
        name='Min Elevation',
        marker_color='orange'
    ))

    fig.update_layout(
        title="Elevation Levels by Bamboo Species",
        xaxis_title="Bamboo Species",
        yaxis_title="Elevation (meters)",
        barmode='group',
    )

    chart_html = plot(fig, output_type='div')
    return chart_html

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
        'elevation_chart': generate_elevation_chart(),
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
