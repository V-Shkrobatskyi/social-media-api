# Generated by Django 5.0.7 on 2024-07-20 18:59

import django.db.models.deletion
import social_network.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Profile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        null=True,
                        upload_to=social_network.models.profile_image_file_path,
                    ),
                ),
                ("bio", models.TextField(blank=True)),
                ("birth_date", models.DateField(blank=True, null=True)),
                (
                    "phone_number",
                    models.CharField(blank=True, max_length=20, null=True),
                ),
                ("hobbies", models.TextField(blank=True)),
                (
                    "followers",
                    models.ManyToManyField(
                        blank=True,
                        related_name="user_followers",
                        to="social_network.profile",
                    ),
                ),
                (
                    "following",
                    models.ManyToManyField(
                        blank=True,
                        related_name="user_following",
                        to="social_network.profile",
                    ),
                ),
                (
                    "owner",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
