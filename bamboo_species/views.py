import pandas as pd
from django.shortcuts import render, get_object_or_404, redirect
from .models import (BambooSpecies, MorphologicalProfile, 
    PhytochemicalProfile, MolecularProfile, SpeciesLocation)
from .forms import SpeciesForm, MorphoForm, PhytochemForm, MolecularForm, CoordForm
from bamboohayan import settings
from django.contrib import messages
from django.utils import timezone
import json, re
from PIL.ExifTags import TAGS, GPSTAGS
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.db import IntegrityError
import json
import datetime
from django.utils.dateparse import parse_date

#########################################
# CRUD: Species Locatiopn Coordinate    #
#########################################
def coord_list(request, species_id=None):
    locations = SpeciesLocation.objects.all()
    if species_id:
        locations = locations.filter(bamboo_species=species_id)

    # Search functionality
    query = request.GET.get('q', '')
    if query:
        locations = locations.filter(
            Q(accession_no__icontains=query) |
            Q(bamboo_species__common_name__icontains=query) |
            Q(coordinate__icontains=query) |
            Q(area_population__icontains=query) |
            Q(collection_date__icontains=query) |
            Q(place__icontains=query)
        )

    # Sorting functionality
    valid_sort_fields = ['accession_no', 'area_population', 'bamboo_species', 'collection_date', 'coordinate', 'place']
    sort_by = request.GET.get('sort_by', 'accession_no')
    if sort_by not in valid_sort_fields:
        sort_by = 'accession_no'

    sort_direction = request.GET.get('sort_direction', 'asc')
    if sort_direction == 'desc':
        locations = locations.order_by(f'-{sort_by}')
    else:
        locations = locations.order_by(sort_by)

    # Pagination functionality
    items_per_page = int(request.GET.get('items_per_page', 5))
    paginator = Paginator(locations, items_per_page)
    page = request.GET.get('page')

    try:
        coords = paginator.page(page)
    except PageNotAnInteger:
        coords = paginator.page(1)
    except EmptyPage:
        coords = paginator.page(paginator.num_pages)

    # Context for the template
    context = {
        'species_locations_json': json.dumps(getLocations(species_id)),
        'coords': coords,
        'species_id': species_id,
        'query': query,
        'sort_by': sort_by,
        'sort_direction': sort_direction,
        'items_per_page': items_per_page,
    }
    return render(request, 'coord/coord_list.html', context)

@login_required
def coord_create(request):
    if request.method == 'POST':
        form = CoordForm(request.POST, request.FILES)
        if form.is_valid():  # This triggers `CoordForm.clean()`
            coord = form.save(commit=False)
            messages.success(request, "Coordinate saved successfully!")
            form.save()
            return redirect('coord-list')
        else:
            messages.error(request, f"Error: {form.errors}")
    else:
        form = CoordForm()

    return render(request, 'coord/coord_form.html', {'form': form, 'editmode': False, 'createMode': True})

def coord_detail(request, pk):
    coord_profile = get_object_or_404(SpeciesLocation, pk=pk)
    form = CoordForm(instance=coord_profile, disable_fields=True)
    return render(request, 'coord/coord_form.html', {'form': form, 'pk': pk})

@login_required
def coord_species_create(request, species_id):
    species = get_object_or_404(BambooSpecies, pk=species_id)
    if request.method=='POST':
        form = CoordForm(request.POST, bamboo_species=species)
        if form.is_valid():
            coord = form.save(commit=False)
            coord.bamboo_species = species
            form.save()
            return redirect('species-detail', species_id=species.pk)
    else:
        form = CoordForm(bamboo_species=species, initial={'bamboo_species': species})
    return render(request, 'coord/coord_form.html', {'form': form, 'species': species, 'createMode': True, 'editmode': False})

@login_required
def upload_coord_data(request, species_id):
    if request.method == 'POST':
        file = request.FILES.get('file')
        if not file:
            messages.error(request, "No file uploaded.")
            return redirect('species-coord-list', species_id=species_id)

        try:
            # Load the file into a DataFrame
            if file.name.endswith('.xlsx'):
                data = pd.read_excel(file)
            elif file.name.endswith('.csv'):
                data = pd.read_csv(file)
            else:
                messages.error(request, "Unsupported file type. Please upload an Excel or CSV file.")
                return redirect('species-coord-list', species_id=species_id)

            # Track the results of processing
            saved_count = 0
            skipped_rows = []

            # Process each row
            for index, row in data.iterrows():
                try:
                    # Clean and validate the collection_date
                    raw_date = row.get('collection_date', None)
                    if pd.isna(raw_date):
                        collection_date = timezone.now().date()
                    elif isinstance(raw_date, datetime.date):
                        collection_date = raw_date
                    else:
                        try:
                            collection_date = parse_date(str(raw_date))
                            if collection_date is None:
                                collection_date = datetime.datetime.strptime(str(raw_date), "%m/%d/%Y").date()
                        except ValueError:
                            raise ValueError(f"Invalid date format for row {index + 1}: {raw_date}")

                    # Attempt to clean the coordinate
                    cleaned_coordinate = clean_coordinates(row.get('coordinate', ''))

                    # Save the valid coordinate to SpeciesLocation
                    SpeciesLocation.objects.create(
                        bamboo_species_id=species_id,
                        coordinate=cleaned_coordinate,
                        accession_no=row.get('accession_no', 'TBA'),
                        area_population=row.get('area_population', 1),
                        collection_date=collection_date,
                        place=row.get('place', ''),
                    )
                    saved_count += 1
                except IntegrityError:
                    # Skip rows with duplicate accession_no
                    # skipped_rows.append((index + 1, f"Duplicate accession_no: {row.get('accession_no')}"))
                    pass
                except ValueError as ve:
                    # Collect rows with invalid data for reporting
                    skipped_rows.append((index + 1, str(ve)))

            # Feedback for the user
            if saved_count > 0:
                messages.success(request, f"Successfully uploaded {saved_count} coordinates.")
            if skipped_rows:
                skipped_message = "\n".join([f"Row {row[0]}: {row[1]}" for row in skipped_rows])
                messages.warning(request, f"Skipped rows:\n{skipped_message}")

        except Exception as e:
            messages.error(request, f"Error processing file: {e}")

    return redirect('species-coord-list', species_id=species_id)

def clean_coordinates(coordinate):
    """
    Cleans and validates GPS coordinates to conform to the format:
    "18.16668°N, 121.74556°E 260Ft"
    """
    try:
        # Step 1: Remove extra spaces
        coordinate = coordinate.strip().replace('  ', ' ')

        # Step 2: Ensure there is a comma between latitude and longitude
        if ',' not in coordinate:
            parts = coordinate.split(' ')
            if len(parts) >= 3:
                lat, lon, elev = parts[0], parts[1], ' '.join(parts[2:])
                coordinate = f"{lat}, {lon} {elev}"

        # Step 3: Ensure the elevation is separate from longitude
        coordinate = re.sub(r"([°][EW])(\d)", r"\1 \2", coordinate)

        # Step 4: Validate the cleaned coordinate using regex
        pattern = r"^\d+\.\d+°[NS], \d+\.\d+°[EW] \d+Ft$"
        if not re.match(pattern, coordinate):
            raise ValueError(f"Invalid coordinate format: '{coordinate}'")

        return coordinate
    except Exception as e:
        print(f"Error cleaning coordinate '{coordinate}': {e}")
        raise ValueError(f"Could not clean coordinate: {coordinate}")

@login_required
def coord_update(request, pk):
    coord_profile = get_object_or_404(SpeciesLocation, pk=pk)
    form = CoordForm(instance=coord_profile)
    if request.method == 'POST':
        form = CoordForm(request.POST, instance=coord_profile)
        if form.is_valid():
            form.save()
            return redirect('coord-list') 
    return render(request, 'coord/coord_form.html', {'form': form, 'pk': pk, 'editMode': True})

@login_required
def coord_delete(request, pk):
    coord_profile = get_object_or_404(SpeciesLocation, pk=pk)
    if request.method == 'POST':
        coord_profile.delete()
        return redirect('coord-list')
    return render(request,'coord/coord_confirm_delete.html', {'data': coord_profile, 'deleteMode': True, 'pk': pk})

#########################################
# CRUD: Bamboo Species                  #
#########################################

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def species_list(request):
    # Get the search query from the request's GET parameters
    query = request.GET.get('q')

    # If a search query is present, filter the queryset accordingly
    if query:
        species_queryset = BambooSpecies.objects.filter(
            Q(common_name__icontains=query) |
            Q(scientific_name__icontains=query) |
            Q(habitat__icontains=query)
        )
    else:
        # If no search query, retrieve all species
        species_queryset = BambooSpecies.objects.all()

    # Add explicit ordering
    species_queryset = species_queryset.order_by('common_name')  # Sort by common name, or choose another field

    # Pagination setup
    items_per_page = 5
    paginator = Paginator(species_queryset, items_per_page)

    page = request.GET.get('page')
    try:
        species = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page.
        species = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver the last page of results.
        species = paginator.page(paginator.num_pages)

    # Pass the species data to the template
    context = {
        'species': species,
    }

    # Render the template with the species data
    return render(request, 'species/species_list.html', context)

def get_gps_coordinates(image_path):
    from PIL import Image, ExifTags

    print("image path:",image_path)
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()

        if not exif_data:
            print("No EXIF metadata found.")
            return None

        gps_info = {}
        for tag, value in exif_data.items():
            decoded_tag = ExifTags.TAGS.get(tag)
            if decoded_tag == "GPSInfo":
                for t in value:
                    gps_tag = ExifTags.GPSTAGS.get(t, t)
                    gps_info[gps_tag] = value[t]

        if not gps_info:
            print("No GPS metadata found.")
            return None

        def convert_to_degrees(value):
            d, m, s = value
            return d + (m / 60.0) + (s / 3600.0)

        latitude = convert_to_degrees(gps_info["GPSLatitude"])
        longitude = convert_to_degrees(gps_info["GPSLongitude"])

        if gps_info["GPSLatitudeRef"] != "N":
            latitude = -latitude
        if gps_info["GPSLongitudeRef"] != "E":
            longitude = -longitude

        return latitude, longitude

    except Exception as e:
        print(f"Error processing GPS data: {e}")
        return None

def parse_coordinates(coordinate):
    try:
        # Step 1: Split by comma to separate latitude and the rest
        lat_part, rest = coordinate.split(",")

        # Step 2: Split the rest to separate longitude and optional elevation
        if " " in rest.strip():
            lon_part, elevation_part = rest.strip().rsplit(" ", 1)
        else:
            lon_part = rest.strip()
            elevation_part = None  # Elevation might be missing

        # Step 3: Clean and extract values
        latitude = lat_part.strip()[:-2]  # Remove °N or °S
        longitude = lon_part.strip()[:-2]  # Remove °E or °W

        # Parse elevation if it exists
        elevation = None
        unit = None
        if elevation_part:
            elevation = elevation_part[:-2]  # Remove unit (Ft or m)
            unit = elevation_part[-2:]  # Extract unit (Ft or m)

        # print(f"Parsed: Latitude={latitude}, Longitude={longitude}, Elevation={elevation}, Unit={unit}")
        return latitude, longitude, elevation

    except ValueError as e:
        raise ValueError(f"Error parsing coordinates '{coordinate}': {e}")

def getLocations(species_id=None):
    if species_id is not None:
        locations = SpeciesLocation.objects.filter(bamboo_species=species_id)
    else:
        locations = SpeciesLocation.objects.all()

    species_locations = []
    for location in locations:
        # print(f"Processing Coordinate: {location.coordinate}")
        try:
            latitude, longitude, elevation = parse_coordinates(location.coordinate)
            species_location = {
                'accession_no': location.accession_no,
                'latitude': latitude,
                'longitude': longitude,
                'elevation': elevation,
                'species': location.bamboo_species.common_name,
                'place': location.place,
                'area_population': location.area_population,
                'marker_icon': location.bamboo_species.marker_icon.url if location.bamboo_species.marker_icon else None,
            }
            species_locations.append(species_location)
        except ValueError as e:
            print(f"Skipping invalid coordinate for location {location.id}: {e}")

    return species_locations

def species_detail(request, species_id):
    context={}
    context['species_id'] = species_id
    context['map_key'] = settings.GOOGLE_API_KEY
    context['species'] =  BambooSpecies.objects.get(id=species_id)
    print(species_id)
    context['species_locations_json'] = json.dumps(getLocations(species_id))
    context['deleteMode']= False
    context['morpho']= MorphologicalProfile.objects.filter(bamboo_species=species_id).first()
    context['phytochem']= PhytochemicalProfile.objects.filter(bamboo_species=species_id).first()
    context['molecular']= MolecularProfile.objects.filter(bamboo_species=species_id).first()

    return render(request, 'species/species_detail.html', context)

@login_required
def species_update(request, species_id):
    bamboo_species = get_object_or_404(BambooSpecies, id = species_id)
    if request.method == 'POST':
        form = SpeciesForm(request.POST, request.FILES, instance=bamboo_species)
        if form.is_valid():
            form.save()
            return redirect('species-detail', species_id = bamboo_species.id)
    else:
        form = SpeciesForm(instance=bamboo_species)
    return render(request, 'species/species_form.html', {'form': form, 'editmode': True})

@login_required
def species_create(request):
    if request.method=='POST':
        form = SpeciesForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('species-list')
    else:
        form = SpeciesForm()
    return render(request, 'species/species_form.html', {'form': form, 'editmode': False})

@login_required
def species_delete(request, species_id):
    bamboo_species = get_object_or_404(BambooSpecies, id = species_id)
    if request.method=='POST':
        bamboo_species.delete()
        return redirect('species-list')
    return render(request, 'species/species_detail.html', {'species': bamboo_species, 'deleteMode': True})

#########################################
# CRUD: Morphological Profile           #
#########################################
def morpho_list(request):
    morpho_profiles = MorphologicalProfile.objects.all().select_related('bamboo_species')
    field_names = [field.name for field in MorphologicalProfile._meta.fields]
    data = list(morpho_profiles.values())
    df = pd.DataFrame(data, columns=field_names)
    return render(request, 'morpho/morpho_list.html', {'df': df})

@login_required
def morpho_create(request, species_id):
    species = get_object_or_404(BambooSpecies, pk=species_id)
    if request.method=='POST':
        form = MorphoForm(request.POST)
        if form.is_valid():
            morpho = form.save(commit=False)
            # morpho.bamboo_species = species
            form.save()
            return redirect('species-detail', species_id)
    else:
        form = MorphoForm(initial={'bamboo_species': species})
    return render(request, 'morpho/morpho_form.html', {'form': form, 'species': species, 'editmode': False})

@login_required
def morpho_update(request, pk):
    morpho_profile = get_object_or_404(MorphologicalProfile, pk=pk)
    form = MorphoForm(instance=morpho_profile)
    if request.method == 'POST':
        form = MorphoForm(request.POST, instance=morpho_profile)
        if form.is_valid():
            form.save()
            return redirect('species-detail', pk )
    return render(request, 'morpho/morpho_form.html', {'form': form})

@login_required   
def morpho_delete(request, pk):
    morpho_profile = get_object_or_404(MorphologicalProfile, pk=pk)
    if request.method == 'POST':
        morpho_profile.delete()
        return redirect('species-detail', pk )
    return render(request,'confirm_delete.html', {'species': morpho_profile, 'deleteMode': True})

#########################################
# CRUD: Phytochemical Profile           #
#########################################
@login_required
def phytochem_create(request, species_id):
    species = get_object_or_404(BambooSpecies, pk=species_id)
    if request.method=='POST':
        form = PhytochemForm(request.POST)
        if form.is_valid():
            phytochem = form.save(commit=False)
            phytochem.bamboo_spaecies = species
            form.save()
            return redirect('species-detail', species_id=species.pk)
    else:
        form = PhytochemForm(initial={'bamboo_species': species})
    return render(request, 'phytochem/phytochem_form.html', {'form': form, 'species': species, 'editmode': False})
@login_required
def phytochem_update(request, pk):
    phytochem_profile = get_object_or_404(PhytochemicalProfile, pk=pk)
    form = PhytochemForm(instance=phytochem_profile)
    if request.method == 'POST':
        form = PhytochemForm(request.POST, instance=phytochem_profile)
        if form.is_valid():
            form.save()
            return redirect('species-detail', pk )
    return render(request, 'phytochem/phytochem_form.html', {'form': form})
@login_required
def phytochem_delete(request, pk):
    phytochem_profile = get_object_or_404(PhytochemicalProfile, pk=pk)
    if request.method == 'POST':
        phytochem_profile.delete()
        return redirect('species-detail', pk )
    return render(request,'confirm_delete.html', {'species': phytochem_profile, 'deleteMode': True})

#########################################
# CRUD: Molecular Profile               #
#########################################
@login_required
def molecular_create(request, species_id):
    species = get_object_or_404(BambooSpecies, pk=species_id)
    if request.method=='POST':
        form = MolecularForm(request.POST)
        if form.is_valid():
            molecular = form.save(commit=False)
            molecular.bamboo_spaecies = species
            form.save()
            return redirect('species-detail', species_id=species.pk)
    else:
        form = MolecularForm(initial={'bamboo_species': species})
    return render(request, 'molecular/molecular_form.html', {'form': form, 'species': species, 'editmode': False})

@login_required
def molecular_update(request, pk):
    molecular_profile = get_object_or_404(MolecularProfile, pk=pk)
    form = MolecularForm(instance=molecular_profile) 
    if request.method == 'POST':
        form = MolecularForm(request.POST, instance=molecular_profile)
        if form.is_valid():
            form.save()
            return redirect('species-detail', pk )
    return render(request, 'molecular/molecular_form.html', {'form': form})

@login_required
def molecular_delete(request, pk):
    molecular_profile = get_object_or_404(MolecularProfile, pk=pk)
    if request.method == 'POST':
        molecular_profile.delete()
        return redirect('species-detail', pk )
    return render(request,'confirm_delete.html', {'species': molecular_profile, 'deleteMode': True})



