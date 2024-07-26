from django.contrib import admin
from social_network.models import Profile, Comment, Post, Like

admin.site.register(Profile)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Like)
