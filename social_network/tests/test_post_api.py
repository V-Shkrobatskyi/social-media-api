import os
import tempfile

from PIL import Image
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from social_network.models import Post, Profile, Comment, Like
from social_network.serializers import (
    PostRetrieveSerializer,
    PostListSerializer,
)

POST_URL = reverse("social_network:post-list")


def sample_post(user, **params) -> Post:
    defaults = {"title": "Test"}
    defaults.update(params)
    return Post.objects.create(user=user, **defaults)


def posts_queryset(**filters):
    return (
        Post.objects.filter(**filters)
        .order_by("-created")
        .annotate(
            likes_count=Count("likes", filter=Q(likes__action="like")),
            dislikes_count=Count("likes", filter=Q(likes__action="dislike")),
        )
    )


def profile_follow_or_unfollow_url(profile_id):
    return reverse("social_network:profile-follow-or-unfollow", args=[profile_id])


def post_add_like_dislike_url(post_id):
    return reverse("social_network:post-add-like-dislike", args=[post_id])


class UnauthenticatedPostApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(POST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedProfileApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = get_user_model().objects.create_user(
            email="test1@test1.com",
            password="TestUser1",
            first_name="test1 FN",
            last_name="test1 LN",
        )
        self.user2 = get_user_model().objects.create_user(
            email="test2@test2.com",
            password="TestUser2",
            first_name="test2 FN",
            last_name="test2 LN",
        )
        self.user3 = get_user_model().objects.create_user(
            email="test3@test3.com",
            password="TestUser3",
            first_name="test3 FN",
            last_name="test3 LN",
        )

        self.profile1 = Profile.objects.create(
            user=self.user1, gender="Male", birth_date="2001-01-01"
        )
        self.profile2 = Profile.objects.create(
            user=self.user2, gender="Female", birth_date="2002-02-02"
        )
        self.profile3 = Profile.objects.create(
            user=self.user3, gender="Female", birth_date="2003-03-03"
        )
        self.client.force_authenticate(self.user1)

    def test_create_post(self):
        payload = {"title": "Test post", "text": "text", "hashtags": "hashtags"}
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            payload.update({"image": ntf})
            res = self.client.post(POST_URL, payload, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        post_from_response = Post.objects.get(id=res.data["id"])

        for key in payload:
            if key != "image":
                self.assertEqual(payload[key], getattr(post_from_response, key))
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(post_from_response.image.path))

    def test_list_posts(self):
        """Users can see only they own posts and posts of users they are following."""
        url = profile_follow_or_unfollow_url(self.profile2.id)
        self.client.get(url)

        for user in (self.user3, self.user2, self.user1):
            self.client.force_authenticate(user)
            sample_post(user)

        res = self.client.get(POST_URL)
        queryset = posts_queryset(user__in=(self.user1, self.user2))
        serializer = PostListSerializer(queryset, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_post_by_text(self):
        text_to_find = "post"
        sample_post(self.user1)
        post2 = sample_post(self.user1, text=f"Test {text_to_find}")
        post3 = Post.objects.create(user=self.user1, title=f"Test {text_to_find}")

        res = self.client.get(POST_URL, {"text": text_to_find})
        queryset = posts_queryset(id__in=(post2.id, post3.id))
        serializer = PostListSerializer(queryset, many=True)

        self.assertEqual(serializer.data, res.data)

    def test_filter_post_by_hashtags(self):
        hashtag_to_find = "post"
        sample_post(self.user1, hashtags=f"Test")
        post2 = sample_post(self.user1, hashtags=f"Test {hashtag_to_find}")

        res = self.client.get(POST_URL, {"hashtags": hashtag_to_find})
        queryset = posts_queryset(id=post2.id)
        serializer = PostListSerializer(queryset, many=True)

        self.assertEqual(serializer.data, res.data)

    def test_retrieve_post_detail(self):
        post1 = sample_post(self.user1)
        url = reverse("social_network:post-detail", args=[post1.id])
        res = self.client.get(url)
        queryset = posts_queryset(id=post1.id)
        serializer = PostRetrieveSerializer(queryset, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(res.data, serializer.data)

    def test_add_comment_post_action(self):
        """This test add comment to the post of user that current user is following."""
        url_follow = profile_follow_or_unfollow_url(self.profile2.id)
        self.client.get(url_follow)
        self.client.force_authenticate(self.user2)
        post = sample_post(self.user2)
        self.client.force_authenticate(self.user1)

        url_add_comment = reverse("social_network:post-add-comment", args=[post.id])
        field = "text"
        payload = {field: "test"}
        res = self.client.post(url_add_comment, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        post_from_response = Comment.objects.get(post=post)
        self.assertEqual(payload[field], getattr(post_from_response, field))

    def test_add_like_post_action(self):
        """This test add like to the post of user that current user is following."""
        url_follow = profile_follow_or_unfollow_url(self.profile2.id)
        self.client.get(url_follow)
        self.client.force_authenticate(self.user2)
        post = sample_post(self.user2)
        self.client.force_authenticate(self.user1)

        url_add_like = post_add_like_dislike_url(post.id)
        field = "action"
        payload = {field: "like"}
        res = self.client.post(url_add_like, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        post_from_response = Like.objects.get(post=post)
        self.assertEqual(payload[field], getattr(post_from_response, field))

    def test_add_dislike_post_action(self):
        """This test change like to dislike to post of user that current user is following."""
        url_follow = profile_follow_or_unfollow_url(self.profile2.id)
        self.client.get(url_follow)
        self.client.force_authenticate(self.user2)
        post = sample_post(self.user2)
        self.client.force_authenticate(self.user1)

        url_add_like = post_add_like_dislike_url(post.id)
        field = "action"
        self.client.post(url_add_like, {field: "like"})
        payload = {field: "dislike"}
        res = self.client.post(url_add_like, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        post_from_response = Like.objects.get(post=post)
        self.assertEqual(payload[field], getattr(post_from_response, field))

    def test_cancel_like_post_action(self):
        """This test cancel like to post of user that current user is following."""
        url_follow = profile_follow_or_unfollow_url(self.profile2.id)
        self.client.get(url_follow)
        self.client.force_authenticate(self.user2)
        post = sample_post(self.user2)
        self.client.force_authenticate(self.user1)

        url_add_like = post_add_like_dislike_url(post.id)
        field = "action"
        self.client.post(url_add_like, {field: "like"})
        payload = {field: "cancel"}
        res = self.client.post(url_add_like, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        post_from_response = Like.objects.get(post=post)
        self.assertEqual(payload[field], getattr(post_from_response, field))

    def test_my_posts_list_posts_action(self):
        """List of user own posts."""
        for user in (self.user1, self.user2, self.user3, self.user1):
            self.client.force_authenticate(user)
            sample_post(user)

        url = reverse("social_network:post-my-posts-list")
        res = self.client.get(url)
        queryset = posts_queryset(user=self.user1)
        serializer = PostListSerializer(queryset, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_liked_posts_list_posts_action(self):
        """List of current user liked posts."""
        sample_post(self.user1)
        posts = []
        for user in (self.user2, self.user1):
            self.client.force_authenticate(user)
            posts.append(sample_post(user))

        field = "action"
        payload = {field: "like"}
        for post in posts:
            url_add_like = post_add_like_dislike_url(post.id)
            self.client.post(url_add_like, payload)

        url = reverse("social_network:post-liked-posts-list")
        res = self.client.get(url)
        queryset = posts_queryset(likes__user=self.user1, likes__action="like")
        serializer = PostListSerializer(queryset, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
