from django.db.models import Count, Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from social_network.models import Profile, Post, Comment, Like
from social_network.permissions import IsOwnerOrIfAuthenticatedReadOnly
from social_network.serializers import (
    ProfileSerializer,
    CommentSerializer,
    PostSerializer,
    ProfileImageSerializer,
    ProfileListSerializer,
    PostListSerializer,
    PostCreateSerializer,
    CommentCreateSerializer,
    LikeSerializer,
    LikeCreateSerializer,
    PostRetrieveSerializer,
)


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = (
        Profile.objects.all()
        .select_related("user")
        .prefetch_related("followers", "following")
    )
    serializer_class = ProfileSerializer
    permission_classes = (IsAuthenticated, IsOwnerOrIfAuthenticatedReadOnly)

    def get_queryset(self):
        first_name = self.request.query_params.get("first_name")
        last_name = self.request.query_params.get("last_name")
        birth_date = self.request.query_params.get("birth_date")
        queryset = self.queryset

        if first_name:
            queryset = queryset.filter(user__first_name__icontains=first_name)
        if last_name:
            queryset = queryset.filter(user__last_name__icontains=last_name)
        if birth_date:
            queryset = queryset.filter(birth_date=birth_date)

        if self.action == "followers":
            profile = self.request.user.profile
            queryset = (
                profile.followers.all()
                .select_related("user")
                .prefetch_related("followers", "following")
            )

        if self.action == "following":
            profile = self.request.user.profile
            queryset = (
                profile.following.all()
                .select_related("user")
                .prefetch_related("followers", "following")
            )

        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                "followers__user",
                "following__user",
            )

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action in ("list", "followers", "following"):
            return ProfileListSerializer
        if self.action == "upload_image":
            return ProfileImageSerializer
        return ProfileSerializer

    def perform_create(self, serializer):
        user = self.request.user
        user.first_name = self.request.data.get("user.first_name")
        user.last_name = self.request.data.get("user.last_name")
        user.save()
        serializer.save(user=user)

    @action(
        methods=["POST", "GET"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsOwnerOrIfAuthenticatedReadOnly],
    )
    def upload_image(self, request, pk=None):
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=["GET"], detail=True)
    def follow_or_unfollow(self, request, pk=None):
        profile = self.get_object()

        if self.request.user.profile == profile:
            return Response(
                {"detail": "You cannot follow/unfollow yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if profile in self.request.user.profile.following.all():
            self.request.user.profile.following.remove(profile)
            return Response(
                {"detail": f"Now you are now unfollowing user {profile}."},
                status=status.HTTP_200_OK,
            )

        self.request.user.profile.following.add(profile)
        return Response(
            {"detail": f"Now you are now following user {profile}."},
            status=status.HTTP_200_OK,
        )

    @action(
        methods=["GET"],
        detail=False,
        url_path="followers",
    )
    def followers(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @action(
        methods=["GET"],
        detail=False,
        url_path="following",
    )
    def following(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "first_name",
                type=OpenApiTypes.STR,
                description="Filter by first_name (ex. ?first_name=a)",
                required=False,
            ),
            OpenApiParameter(
                "last_name",
                type=OpenApiTypes.STR,
                description="Filter by last_name (ex. ?last_name=a)",
                required=False,
            ),
            OpenApiParameter(
                name="birth_date",
                type=OpenApiTypes.DATE,
                description="Filter by birth_date " "(ex. ?birth_date=2014-08-21)",
                required=False,
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class PostViewSet(viewsets.ModelViewSet):
    queryset = (
        Post.objects.all()
        .select_related("user")
        .prefetch_related(
            "likes",
            "comments__user",
        )
        .annotate(
            likes_count=Count("likes", filter=Q(likes__action="like")),
            dislikes_count=Count("likes", filter=Q(likes__action="dislike")),
        )
    ).order_by("-created")
    serializer_class = PostSerializer
    permission_classes = (IsAuthenticated, IsOwnerOrIfAuthenticatedReadOnly)

    def get_queryset(self):
        queryset = self.queryset

        if self.action in ("list", "my_posts_list", "liked_posts_list"):

            if self.action == "list":
                queryset = self.queryset.filter(
                    Q(user__profile__followers=self.request.user.profile)
                    | Q(user__profile=self.request.user.profile)
                )

            if self.action == "my_posts_list":
                queryset = self.queryset.filter(user__profile=self.request.user.profile)

            if self.action == "liked_posts_list":
                queryset = self.queryset.filter(
                    likes__user=self.request.user, likes__action="like"
                )

            text = self.request.query_params.get("text")
            hashtag = self.request.query_params.get("hashtag")

            if text:
                queryset = queryset.filter(
                    Q(title__icontains=text) | Q(text__icontains=text)
                )
            if hashtag:
                queryset = queryset.filter(hashtags__icontains=hashtag)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action in ("list", "my_posts_list", "liked_posts_list"):
            return PostListSerializer
        if self.action == "add_comment":
            return CommentSerializer
        if self.action == "add_like_dislike":
            return LikeSerializer
        if self.action == "create":
            return PostCreateSerializer
        if self.action == "retrieve":
            return PostRetrieveSerializer
        return PostSerializer

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

    def perform_update(self, serializer):
        user = self.request.user
        serializer.save(user=user)

    @action(
        detail=True,
        methods=["POST"],
        url_path="add_comment",
        permission_classes=[IsAuthenticated],
    )
    def add_comment(self, request, pk=None):
        post = self.get_object()
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, post=post)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["POST"],
        url_path="add_like_dislike",
        permission_classes=[IsAuthenticated],
    )
    def add_like_dislike(self, request, pk=None):
        post = self.get_object()
        serializer = LikeCreateSerializer(
            data=request.data, context={"request": request, "post": post}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, post=post)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        methods=["GET"],
        detail=False,
        url_path="my_posts_list",
    )
    def my_posts_list(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @action(
        methods=["GET"],
        detail=False,
        url_path="liked_posts_list",
    )
    def liked_posts_list(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "text",
                type=OpenApiTypes.STR,
                description="Filter by post title and text (ex. ?text=a)",
                required=False,
            ),
            OpenApiParameter(
                "hashtag",
                type=OpenApiTypes.STR,
                description="Filter by hashtag (ex. ?hashtag=a)",
                required=False,
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class CommentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Comment.objects.all().select_related("user", "post")
    serializer_class = CommentSerializer
    permission_classes = (IsAuthenticated, IsOwnerOrIfAuthenticatedReadOnly)


class LikeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Like.objects.all().select_related("user", "post")
    serializer_class = LikeSerializer
    permission_classes = (IsAuthenticated, IsOwnerOrIfAuthenticatedReadOnly)
