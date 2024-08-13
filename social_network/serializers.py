from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from social_network.models import Profile, Comment, Like, Post
from user.serializers import UserUpdateProfileSerializer


class ProfileSerializer(serializers.ModelSerializer):
    user = UserUpdateProfileSerializer(many=False, partial=True)
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
            raise ValidationError({"error": "You already have your own profile."})

        return data

    def update(self, instance, validated_data):
        fields_to_update = ["gender", "bio", "phone_number"]

        for field in fields_to_update:
            value = validated_data.get(field, getattr(instance, field))
            setattr(instance, field, value)

        instance.save()

        user = instance.user
        user_data = self.validated_data.get("user")
        user.first_name = user_data["first_name"]
        user.last_name = user_data["last_name"]

        user.save()

        return instance


class ProfileListSerializer(serializers.ModelSerializer):
    following_count = serializers.IntegerField(source="following.count")
    followers_count = serializers.IntegerField(source="followers.count")

    class Meta:
        model = Profile
        fields = (
            "id",
            "full_name",
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


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.CharField(read_only=True, source="user.full_name")
    post = serializers.CharField(read_only=True, source="post.title")

    class Meta:
        model = Comment
        fields = ("id", "post", "user", "text", "created")


class CommentCreateSerializer(CommentSerializer):
    class Meta:
        model = Comment
        fields = ("text",)


class CommentDetailForPostSerializer(CommentSerializer):
    user = serializers.CharField(read_only=True, source="user.full_name")

    class Meta:
        model = Comment
        fields = ("user", "text", "created")


class PostSerializer(serializers.ModelSerializer):
    user = serializers.CharField(read_only=True, source="user.full_name")
    comments = CommentDetailForPostSerializer(many=True, read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    dislikes_count = serializers.IntegerField(read_only=True)

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
            "likes_count",
            "dislikes_count",
        )
        read_only_fields = ("id", "comments")


class PostCreateSerializer(PostSerializer):
    class Meta:
        model = Post
        fields = (
            "id",
            "title",
            "image",
            "text",
            "hashtags",
        )


class PostListSerializer(serializers.ModelSerializer):
    user = serializers.CharField(read_only=True, source="user.full_name")
    likes_count = serializers.IntegerField()
    dislikes_count = serializers.IntegerField()

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
            "comments_count",
            "likes_count",
            "dislikes_count",
        )


class LikeSerializer(serializers.ModelSerializer):
    user = serializers.CharField(read_only=True, source="user.full_name")
    post = serializers.CharField(read_only=True, source="post.title")

    class Meta:
        model = Like
        fields = ("id", "post", "action", "user")


class LikeCreateSerializer(LikeSerializer):
    class Meta:
        model = Like
        fields = ("action",)

    def validate(self, attrs):
        data = super(LikeCreateSerializer, self).validate(attrs)
        post = self.context["post"]
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
        post = self.context["post"]
        action = self.validated_data["action"]
        user = self.context["request"].user

        like, created = Like.objects.get_or_create(
            user=user, post=post, defaults={"action": action}
        )
        if not created:
            like.action = action
            like.save()

        return like
