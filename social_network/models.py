import os
import uuid
from django.utils.text import slugify
from django.db import models
from social_media_api import settings


def profile_image_file_path(instance, filename):
    extension = os.path.splitext(filename)
    filename = f"{slugify(instance.owner)}-{uuid.uuid4()}{extension}"

    return os.path.join("uploads/profile_images/", filename)


class Profile(models.Model):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    image = models.ImageField(null=True, upload_to=profile_image_file_path)
    bio = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=12, null=True, blank=True)
    hobbies = models.TextField(blank=True)
    following = models.ManyToManyField("self", blank=True, related_name="following")
    followers = models.ManyToManyField("self", blank=True, related_name="followers")

    def __str__(self) -> str:
        return self.owner.username
