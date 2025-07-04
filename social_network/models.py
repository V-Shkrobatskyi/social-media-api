import os
import uuid

from django.utils.text import slugify
from django.db import models
from social_media_api import settings


def image_file_path(instance, filename):
    extension = os.path.splitext(filename)
    filename = f"{slugify(instance.user)}-{uuid.uuid4()}{extension}"

    return os.path.join(f"uploads/{instance.__class__.__name__.lower()}/", filename)


class Profile(models.Model):
    class GenderChoices(models.TextChoices):
        MALE = "Male"
        FEMALE = "Female"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    image = models.ImageField(null=True, upload_to=image_file_path)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=15, choices=GenderChoices.choices)
    bio = models.TextField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=12, null=True, blank=True)
    following = models.ManyToManyField(
        "self", blank=True, symmetrical=False, related_name="followers"
    )

    @property
    def full_name(self) -> str:
        return str(self.user.full_name)

    def __str__(self):
        return str(self.user.full_name)


class Post(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    image = models.ImageField(null=True, upload_to=image_file_path, blank=True)
    title = models.CharField(max_length=255)
    text = models.TextField()
    hashtags = models.CharField(max_length=125, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["-created"]

    @property
    def comments_count(self):
        return self.comments.count()


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    text = models.TextField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text

    class Meta:
        ordering = ["-created"]


class Like(models.Model):
    class ActionChoices(models.TextChoices):
        LIKE = "like"
        CANCEL = "cancel"
        DISLIKE = "dislike"

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="likes",
    )
    action = models.CharField(max_length=15, choices=ActionChoices.choices)
