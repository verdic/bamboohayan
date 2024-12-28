from django.db import models
from django.utils import timezone
from django_countries.fields import CountryField

# Create your models here.
class BambooSpecies(models.Model):
    common_name = models.CharField(max_length=100)                                      # Common Name
    scientific_name = models.CharField(max_length=100)                                  # Scientific name
    origin =  CountryField()                                                            # Origin
    uses = models.TextField(null=True)                                  # uses
    propagation = models.CharField(max_length=120, null=True, blank=True,)              # propagation
    rhyzome_type = models.CharField(max_length=50, null=True, blank=True,)              # rhyzome type
    habitat = models.TextField()                                                        # habitat
    image = models.ImageField(upload_to='bamboo_species', blank=True, null=True)
    marker_icon = models.ImageField(upload_to='marker_icons', null=True, blank=True)

    def __str__(self):
        return self.common_name

    class meta:
        db_table = "Species"

class SpeciesLocation(models.Model):
    # id = models.BigAutoField(primary_key=True )
    accession_no = models.CharField(max_length=7, primary_key=True)
    bamboo_species = models.ForeignKey(BambooSpecies, on_delete=models.CASCADE, related_name='bamboo_species_location_profile')
    coordinate = models.CharField(max_length=100, default='18.16668°N 121.74556°E 260Ft')
    area_population = models.SmallIntegerField(default=1)               # area population
    collection_date = models.DateField(default = timezone.now)          # collection date
    place = models.CharField(max_length=80, null=True)                  # place
    # type_of_ecosystem = models.CharField(max_length=255,null=True)      # ecosystem

class MorphologicalProfile(models.Model):
    bamboo_species = models.OneToOneField(BambooSpecies, on_delete=models.CASCADE, primary_key=True, related_name='bamboo_species_morpho_profile')
    culm_base = models.TextField()                                                  # culm base
    branching = models.CharField(max_length=50)                                     # branching
    habit = models.CharField(max_length=50)                                         # habit
    culm_internodes = models.CharField(max_length=30)                               # culm internodes
    primary_buds_per_mid_culm_node = models.IntegerField()                          # primary buds per mid culm node
    culm_leaves = models.CharField(max_length=100)                                  # culm leaves
    internode_length_relative = models.TextField()                                  #  internode length relative
    internode_length = models.FloatField()                                          # internode length
    internode_width = models.FloatField()                                           # internode width
    nodal_line_position = models.CharField(max_length=40)                           # nodal line position
    nodal_line_diameter = models.CharField(max_length=60)                           #  nodal line diameter
    culm_color_appearance = models.CharField(max_length=15)                         # culm color appearance
    leaf_color_appearance = models.CharField(max_length=15)                         # leaf color appearance
    shoot_location_of_trichomes_in_culm_sheath = models.CharField(max_length=20)    # shoot_location_of_trichomes_in_culm_sheath
    shoot_concentration_of_trichomes_in_culm_sheath = models.CharField(max_length=20) # shoot concentration of trichomes in culm sheath
    shoot_culm_sheath_color = models.CharField(max_length=60)                       # shoot culm sheath color
    branch_initiation_development = models.CharField(max_length=120)                # branch initiation development
    branching_pattern = models.CharField(max_length=15)                             # branching pattern
    incidence_of_flowering = models.CharField(max_length=100)                        # incidence of flowering
    inner_stem_appearance = models.CharField(max_length=30)                         # inner stem appearance

    def __str__(self):
        return self.bamboo_species

    class Meta:
        db_table = 'MorphologicalProfile' 

class PhytochemicalProfile(models.Model):
    bamboo_species = models.OneToOneField(BambooSpecies, on_delete=models.CASCADE, primary_key=True, related_name='bamboo_species_phytochem_profile')
    anthocyanin = models.CharField(max_length=20)
    carotenoids = models.CharField(max_length=20)
    coumarins = models.CharField(max_length=20)
    flavonoids = models.CharField(max_length=20)
    phenols = models.CharField(max_length=20)
    quinones = models.CharField(max_length=20)
    saponins = models.CharField(max_length=20)
    steroids = models.CharField(max_length=20)
    tannins = models.CharField(max_length=20)
    terpenoids = models.CharField(max_length=20)

    def __str__(self):
        return self.bamboo_species

    class Meta:
        db_table = 'PhytochemicalProfile' 

class MolecularProfile(models.Model):
    bamboo_species = models.OneToOneField(BambooSpecies, on_delete=models.CASCADE, primary_key=True, related_name='bamboo_species_molecular_profile')
    morpho_family=models.CharField(max_length=25)                   # morpho family
    morpho_genus=models.CharField(max_length=40)                    # morpho genus
    morpho_species=models.CharField(max_length=40)                  # morpho species
    morpho_variety=models.CharField(max_length=25, null=True)       # morpho variety
    dna_rbcl_family=models.CharField(max_length=25)                 # dna rbcl family
    dna_rbcl_genus=models.CharField(max_length=40)                  # dna rbcl genus
    dna_rbcl_species=models.CharField(max_length=40)                # dna rbcl species
    dna_rbcl_variety=models.CharField(max_length=25, null=True)     # dna rbcl variety
    dna_query_length = models.IntegerField()                        # dna query length
    percentage_identification= models.FloatField()                  # percentage identification
    
    def __str__(self):
        return self.bamboo_species

    class Meta:
        db_table = 'MolecularProfile' 

        
    

