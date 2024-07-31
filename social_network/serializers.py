from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from social_network.models import Profile, Comment, Like, Post


class ProfileSerializer(serializers.ModelSerializer):
    following = serializers.SerializerMethodField()
    followers = serializers.SerializerMethodField()

    def get_following(self, obj):
        return [following.full_name for following in obj.following.all()]

    def get_followers(self, obj):
        return [follower.full_name for follower in obj.followers.all()]

    class Meta:
        model = Profile
        fields = [
            "id",
            "user",
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
        read_only_fields = ("id", "user", "following")

    def validate(self, attrs):
        data = super(ProfileSerializer, self).validate(attrs=attrs)

        user = self.context["request"].user
        profile_exist = Profile.objects.filter(user=user).first()
        if profile_exist and self.instance != profile_exist:
            raise ValidationError(
                {
                    "error": "You already have your own profile. You can change only your profile."
                }
            )

        return data

    def create(self, validated_data):
        profile = Profile.objects.create(**validated_data)
        return profile

    def update(self, instance, validated_data):
        fields_to_update = ["last_name", "bio", "phone_number"]

        for field in fields_to_update:
            value = validated_data.get(field, getattr(instance, field))
            setattr(instance, field, value)

        instance.save()
        return instance


class ProfileListSerializer(serializers.ModelSerializer):
    following_count = serializers.IntegerField(source="following.count")
    followers_count = serializers.IntegerField(source="followers.count")

    class Meta:
        model = Profile
        fields = (
            "id",
            "first_name",
            "last_name",
            "birth_date",
            "gender",
            "bio",
            "phone_number",
            "following_count",
            "followers_count",
        )


class ProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("id", "image")

    def validate(self, attrs):
        data = super(ProfileImageSerializer, self).validate(attrs=attrs)

        user = self.context["request"].user
        profile_user = Profile.objects.filter(user=user).first()

        if profile_user != user:
            raise ValidationError(
                {"error": "You can upload image only to your profile."}
            )

        return data


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ("id", "text", "user", "created")


class CommentCreateSerializer(CommentSerializer):
    class Meta:
        model = Comment
        fields = ("id", "post", "text", "created")


class CommentDetailSerializer(CommentSerializer):
    class Meta:
        model = Comment
        fields = ("id", "post", "user", "text", "created")


class PostSerializer(serializers.ModelSerializer):
    user = serializers.CharField(read_only=True, source="user.profile.full_name")
    comments = CommentSerializer(many=True, read_only=True)
    likes = serializers.CharField(read_only=True, source="like.likes_count")
    dislikes = serializers.CharField(read_only=True, source="like.dislikes_count")

    class Meta:
        model = Post
        fields = (
            "id",
            "title",
            "image",
            "text",
            "hashtags",
            "user",
            "created",
            "comments",
            "likes",
            "dislikes",
        )


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ("id", "post", "action", "user")
        read_only_fields = ("id", "user")

    def validate(self, attrs):
        data = super(LikeSerializer, self).validate(attrs)
        post = attrs["post"]
        action = attrs["action"]
        user = self.context["request"].user

        if Like.objects.filter(
            post=post,
            user=user,
            action=action,
        ).exists():
            raise serializers.ValidationError(f"You have already {action} this post.")

        return data

    def save(self, *args, **kwargs):
        post = self.validated_data["post"]
        action = self.validated_data["action"]
        user = self.context["request"].user
        like_instance = Like.objects.filter(
            post=post,
            user=user,
            action=action,
        )

        if like_instance.exists():
            like_instance(action=action).save()
        else:
            Like.objects.create(user=user, post=post, action=action)
