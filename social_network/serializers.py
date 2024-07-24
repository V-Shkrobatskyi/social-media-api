from rest_framework import serializers

from social_network.models import Profile, Comment, Like, Post


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


class ProfileListSerializer(serializers.ModelSerializer):
    count_following = serializers.IntegerField(source="following.count")
    count_followers = serializers.IntegerField(source="followers.count")

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
            "count_following",
            "count_followers",
        )


class ProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("id", "image")


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
    comments = CommentSerializer(many=True, read_only=True)
    likes = serializers.CharField(read_only=True, source="like.likes_count")
    dislikes = serializers.CharField(read_only=True, source="like.dislikes_count")

    class Meta:
        model = Post
        fields = (
            "id",
            "text",
            "created_at",
            "hashtag",
            "image",
            "comments",
            "likes",
            "scheduled_time",
        )


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ("id", "post", "action", "user")

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
