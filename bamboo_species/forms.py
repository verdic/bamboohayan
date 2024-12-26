from django import forms
from .models import SpeciesLocation, BambooSpecies, MorphologicalProfile, PhytochemicalProfile, MolecularProfile
from django_countries.fields import CountryField
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from django.core.files.storage import default_storage

class SpeciesForm(forms.ModelForm):
    image = forms.ImageField(widget=forms.ClearableFileInput())
    marker_icon = forms.ImageField(widget=forms.ClearableFileInput())
    origin = CountryField().formfield(initial='PH')  # Set the initial value to 'PH' for Philippines

    class Meta:
        model = BambooSpecies
        fields = '__all__'

        widgets = {
            'common_name': forms.TextInput(),
            'scientific_name': forms.TextInput(),
            'habitat': forms.Textarea(),
         }

        labels = {
            'common_name': 'Common Name',
            'scientific_name': 'Scientific Name',
            'habitat': 'Habitat',
            'marker_icon': 'Marker Icon (Optional: to be used in mapping)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].widget.attrs['accept'] = 'image/*'


class CoordForm(forms.ModelForm):
    geotagged_photo = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        label="Upload Geotagged Photo (Optional)"
    )

    coordinate = forms.CharField(
        required=False,  # No longer required at the form level
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter coordinates (e.g., 18.16668°N, 121.74556°E 260Ft)',
        }),
        label="Coordinates"
    )

    collection_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'type': 'date',  # Use 'text' to let the JavaScript datepicker override the default behavior
                'class': 'datepicker',  # Class for targeting by the JS datepicker library
                'placeholder': 'Select a date',
            }
        ),
        label="Collection Date"
    )

    class Meta:
        model = SpeciesLocation
        fields = ['bamboo_species', 'accession_no', 'coordinate', 'area_population', 'collection_date', 'place']

    def clean(self):
        cleaned_data = super().clean()
        geotagged_photo = cleaned_data.get("geotagged_photo")
        coordinate = cleaned_data.get("coordinate")

        # Validate geotagged photo and extract GPS metadata
        if geotagged_photo:
            try:
                temp_file_path = default_storage.save(geotagged_photo.name, geotagged_photo)
                from .views import get_gps_coordinates
                gps_data = get_gps_coordinates(temp_file_path)

                if gps_data:
                    latitude, longitude = gps_data
                    cleaned_data["coordinate"] = f"{latitude:.6f}°N, {longitude:.6f}°E"
                else:
                    raise forms.ValidationError("The uploaded photo does not contain geotagging data.")
            except Exception as e:
                raise forms.ValidationError(f"Error processing geotagged photo: {e}")
            finally:
                default_storage.delete(temp_file_path)

        # Ensure either coordinate or geotagged photo is provided
        elif not coordinate:
            raise forms.ValidationError("Please provide coordinates or upload a geotagged photo.")

        return cleaned_data
    
    def __init__(self, *args, **kwargs):
        if 'bamboo_species' in kwargs:
            bamboo_species = kwargs.pop('bamboo_species', None)
        else:
            bamboo_species = BambooSpecies.objects.all()

        disable_fields = kwargs.pop('disable_fields', False)
        
        super().__init__(*args, **kwargs)
        super(CoordForm, self).__init__(*args, **kwargs)
        self.fields['bamboo_species'].quesryset = bamboo_species

        if disable_fields:
             for field in self.fields.values():
                field.disabled = True

    def get_initial(self):
        initial = super().get_initial()
        initial['bamboo_species'] = self.kwargs.get('pk')
        return initial


class MorphoForm(forms.ModelForm):
    class Meta:
        model = MorphologicalProfile
        fields = '__all__'

        widgets = {
            'culm_base': forms.TextInput(),
            'branching': forms.TextInput(),
            'habit': forms.TextInput(),
            'culm_internodes': forms.TextInput(),
            'primary_buds_per_mid_culm_node': forms.NumberInput(),
            'culm_leaves': forms.TextInput(),
            'internode_length_relative': forms.TextInput(),
            'internode_length': forms.NumberInput(),
            'internode_width': forms.NumberInput(),
            'nodal_line_position': forms.TextInput(),
            'nodal_line_diameter': forms.TextInput(),
            'culm_color_appearance': forms.TextInput(),
            'leaf_color_appearance': forms.TextInput(),
            'shoot_location_of_trichomes_in_culm_sheath': forms.TextInput(),
            'shoot_concentration_of_trichomes_in_culm_sheath': forms.TextInput(),
            'shoot_culm_sheath_color': forms.TextInput(),
            'branch_initiation_development': forms.TextInput(),
            'branching_pattern': forms.TextInput(),
            'incidence_of_flowering': forms.TextInput(),
            'inner_stem_appearance': forms.TextInput(),
        }

        labels = {
            'culm_base': 'Culm base morphology',
            'branching': 'Culm base branching(tillering)',
            'habit': 'Habit',
            'culm_internodes': 'Culm internodes',
            'primary_buds_per_mid_culm_node': 'Primary buds per mid-culm node',
            'culm_leaves': 'Culm leaves / girdle',
            'internode_length_relative': ' Internode length (relative)',
            'internode_length': 'Numerical measurement of internode length (cm)',
            'internode_width': 'Numerical measurement of internode width (cm)',
            'nodal_line_position': 'Nodal line position',
            'nodal_line_diameter': 'Nodal line diameter',
            'culm_color_appearance': 'Stem/culm color and appearance',
            'leaf_color_appearance': 'Leaf color and appearance',
            'shoot_location_of_trichomes_in_culm_sheath': 'Location of trichomes in culm sheath',
            'shoot_concentration_of_trichomes_in_culm_sheath': 'Concentration of trichomes in culm sheath',
            'shoot_culm_sheath_color': 'Culm sheath color',
            'branch_initiation_development': 'Branch initiation/development',
            'branching_pattern': 'Branching pattern',
            'incidence_of_flowering': 'Incidence of flowering',
            'inner_stem_appearance': 'Inner stem appearance',
        }

    def __init__(self, *args, **kwargs):
        bamboo_species = kwargs.pop('bamboo_species', None)
        super().__init__(*args, **kwargs)
        super(MorphoForm, self).__init__(*args, **kwargs)
        if bamboo_species:
            self.initial['bamboo_species'] = bamboo_species
            self.fields['bamboo_species'].disabled = True


    def get_initial(self):
        initial = super().get_initial()
        initial['bamboo_species'] = self.kwargs.get('pk')
        return initial

class PhytochemForm(forms.ModelForm):
    CHOICES = [('Absent','Absent'),
        ('Slightly Present', 'Slightly Present'),
        ('Moderately Present','Moderately Present'),
        ('Highly Present', 'Highly Present')
    ]

    anthocyanin = forms.ChoiceField(choices=CHOICES, widget=forms.Select)
    carotenoids = forms.ChoiceField(choices=CHOICES, widget=forms.Select)
    coumarins = forms.ChoiceField(choices=CHOICES, widget=forms.Select)
    flavonoids = forms.ChoiceField(choices=CHOICES, widget=forms.Select)
    phenols = forms.ChoiceField(choices=CHOICES, widget=forms.Select)
    quinones = forms.ChoiceField(choices=CHOICES, widget=forms.Select)
    saponins = forms.ChoiceField(choices=CHOICES, widget=forms.Select)
    steroids = forms.ChoiceField(choices=CHOICES, widget=forms.Select)
    tannins = forms.ChoiceField(choices=CHOICES, widget=forms.Select)
    terpenoids = forms.ChoiceField(choices=CHOICES, widget=forms.Select)

    class Meta:
        model = PhytochemicalProfile
        fields = '__all__'

        labels = {
            'anthocyanin': 'Anthocyanin',
            'carotenoids': 'Carotenoids',
            'coumarins': 'Coumarins',
            'flavonoids': 'Flavonoids',
            'phenols': 'Phenols',
            'quinones': 'Quinones',
            'saponins': 'Saponins',
            'steroids': 'Steroids',
            'tannins': 'Tannins',
            'terpenoids': 'terpenoids',
        }

    def __init__(self, *args, **kwargs):
        bamboo_species = kwargs.pop('bamboo_species', None)
        super().__init__(*args, **kwargs)
        super(PhytochemForm, self).__init__(*args, **kwargs)
        if bamboo_species:
            self.initial['bamboo_species'] = bamboo_species
            self.fields['bamboo_species'].disabled = True


    def get_initial(self):
        initial = super().get_initial()
        initial['bamboo_species'] = self.kwargs.get('pk')
        return initial

class MolecularForm(forms.ModelForm):
    class Meta:
        model = MolecularProfile
        fields = '__all__'
        widgets = {
            'morpho_family': forms.TextInput(),
            'morpho_genus': forms.TextInput(),
            'morpho_species': forms.TextInput(),
            'morpho_variety': forms.TextInput(),
            'dna_rbcl_family': forms.TextInput(),
            'dna_rbcl_genus': forms.TextInput(),
            'dna_rbcl_species': forms.TextInput(),
            'dna_rbcl_variety': forms.TextInput(),
            'dna_query_length': forms.NumberInput(),
            'percentage_identification':forms.NumberInput(),

        }

        labels = {
            'morpho_family': 'Morphological Family',
            'morpho_genus': 'Morphological Genus',
            'morpho_species': 'Morphogical Species',
            'morpho_variety': 'Morphological Variety',
            'dna_rbcl_morpho_family':  'DNA rcbL Gene Family',
            'dna_rbcl_morpho_genus':   'DNA rcbL Gene Genus',
            'dna_rbcl_morpho_species': 'DNA rcbL Gene Species',
            'dna_rbcl_morpho_variety': 'DNA rcbL Gene Variety',
            'dna_query_length': 'DNA Query Length',
            'percentage_identification': 'Percentage Identification',
        }

    def __init__(self, *args, **kwargs):
        bamboo_species = kwargs.pop('bamboo_species', None)
        super().__init__(*args, **kwargs)
        super(MolecularForm, self).__init__(*args, **kwargs)
        if bamboo_species:
            self.initial['bamboo_species'] = bamboo_species
            self.fields['bamboo_species'].disabled = True


    def get_initial(self):
        initial = super().get_initial()
        initial['bamboo_species'] = self.kwargs.get('pk')
        return initial

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['morpho_variety'].required = False
        self.fields['dna_rbcl_variety'].required = False
