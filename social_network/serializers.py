from rest_framework import serializers

from social_network.models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "id",
            "first_name",
            "last_name",
            "image",
            "birth_date",
            "gender",
            "bio",
            "phone_number",
            "following",
            "followers",
        ]
