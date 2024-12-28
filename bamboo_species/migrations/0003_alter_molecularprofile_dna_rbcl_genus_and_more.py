# Generated by Django 5.0.4 on 2024-12-28 14:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bamboo_species", "0002_alter_morphologicalprofile_incidence_of_flowering"),
    ]

    operations = [
        migrations.AlterField(
            model_name="molecularprofile",
            name="dna_rbcl_genus",
            field=models.CharField(max_length=40),
        ),
        migrations.AlterField(
            model_name="molecularprofile",
            name="dna_rbcl_species",
            field=models.CharField(max_length=40),
        ),
        migrations.AlterField(
            model_name="molecularprofile",
            name="morpho_genus",
            field=models.CharField(max_length=40),
        ),
        migrations.AlterField(
            model_name="molecularprofile",
            name="morpho_species",
            field=models.CharField(max_length=40),
        ),
        migrations.AlterField(
            model_name="morphologicalprofile",
            name="nodal_line_position",
            field=models.CharField(max_length=40),
        ),
    ]