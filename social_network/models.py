import os
import uuid

from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.db import models
from social_media_api import settings


def profile_image_file_path(instance, filename):
    extension = os.path.splitext(filename)
    filename = f"{slugify(instance.user)}-{uuid.uuid4()}{extension}"

    return os.path.join("uploads/profile_images/", filename)


class Profile(models.Model):
    class GenderChoices(models.TextChoices):
        MALE = "Male"
        FEMALE = "Female"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    image = models.ImageField(null=True, upload_to=profile_image_file_path)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=15, choices=GenderChoices.choices)
    bio = models.TextField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=12, null=True, blank=True)
    following = models.ManyToManyField(
        "self", blank=True, symmetrical=False, related_name="profile_following"
    )
    followers = models.ManyToManyField(
        "self", blank=True, symmetrical=False, related_name="profile_followers"
    )

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"
