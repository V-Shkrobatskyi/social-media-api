from rest_framework import viewsets, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from social_network.models import Profile, Post, Comment, Like
from social_network.serializers import (
    ProfileSerializer,
    CommentSerializer,
    PostSerializer,
    ProfileImageSerializer,
    ProfileListSerializer,
    LikeSerializer,
)


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all().prefetch_related("followers", "following")
    serializer_class = ProfileSerializer

    def get_queryset(self):
        first_name = self.request.query_params.get("first_name")
        last_name = self.request.query_params.get("last_name")
        birth_date = self.request.query_params.get("birth_date")
        queryset = self.queryset

        if first_name:
            queryset = queryset.filter(first_name__icontains=first_name)
        if last_name:
            queryset = queryset.filter(last_name__icontains=last_name)
        if birth_date:
            queryset = queryset.filter(birth_date=birth_date)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return ProfileListSerializer
        if self.action == "upload_image":
            return ProfileImageSerializer
        return ProfileSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    def upload_image(self, request, pk=None):
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().select_related("user").prefetch_related("comments")
    serializer_class = PostSerializer


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer


class LikeViewSet(viewsets.ModelViewSet):
    queryset = Like.objects.all().select_related("user", "post")
    serializer_class = LikeSerializer

    def perform_create(self, serializer):
        post = get_object_or_404(Post, pk=self.request.data["post"])
        user = self.request.user

        likes = Like.objects.filter(user=user, post=post)
        if likes:
            likes.delete()
        else:
            serializer.save(user=user, post=post)
