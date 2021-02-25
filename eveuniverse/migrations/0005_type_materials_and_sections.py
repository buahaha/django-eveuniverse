# Generated by Django 3.1.6 on 2021-02-25 18:10

import bitfield.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("eveuniverse", "0004_effect_longer_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="eveplanet",
            name="enabled_sections",
            field=bitfield.models.BitField(
                ("asteroid_belts", "moons"),
                default=None,
                help_text="Flags for loadable sections. True if instance was loaded with section.",
            ),
        ),
        migrations.AddField(
            model_name="evesolarsystem",
            name="enabled_sections",
            field=bitfield.models.BitField(
                ("planets", "stargates", "stars", "stations"),
                default=None,
                help_text="Flags for loadable sections. True if instance was loaded with section.",
            ),
        ),
        migrations.AddField(
            model_name="evetype",
            name="enabled_sections",
            field=bitfield.models.BitField(
                ("dogmas", "graphics", "market_groups", "type_materials"),
                default=None,
                help_text="Flags for loadable sections. True if instance was loaded with section.",
            ),
        ),
        migrations.CreateModel(
            name="EveTypeMaterial",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("quantity", models.PositiveIntegerField()),
                (
                    "eve_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="materials",
                        to="eveuniverse.evetype",
                    ),
                ),
                (
                    "material_eve_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="material_types",
                        to="eveuniverse.evetype",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="evetypematerial",
            constraint=models.UniqueConstraint(
                fields=("eve_type", "material_eve_type"), name="fpk_evetypematerial"
            ),
        ),
    ]
