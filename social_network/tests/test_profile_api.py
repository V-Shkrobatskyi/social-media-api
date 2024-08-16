import os
import tempfile

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from social_network.models import Profile
from social_network.serializers import (
    ProfileSerializer,
    ProfileListSerializer,
)

PROFILE_URL = reverse("social_network:profile-list")


def profile_follow_or_unfollow_url(profile_id):
    return reverse("social_network:profile-follow-or-unfollow", args=[profile_id])


class UnauthenticatedProfileApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(PROFILE_URL)
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

    def test_list_profiles(self):
        res = self.client.get(PROFILE_URL)
        profiles = Profile.objects.order_by("id")
        serializer = ProfileListSerializer(profiles, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_profile_by_first_name(self):
        response = self.client.get(PROFILE_URL, {"first_name": "test1"})

        serializer1 = ProfileListSerializer(self.profile1)
        serializer2 = ProfileListSerializer(self.profile2)

        self.assertIn(serializer1.data, response.data)
        self.assertNotIn(serializer2.data, response.data)

    def test_filter_profile_by_last_name(self):
        response = self.client.get(PROFILE_URL, {"last_name": "test1"})

        serializer1 = ProfileListSerializer(self.profile1)
        serializer2 = ProfileListSerializer(self.profile2)

        self.assertIn(serializer1.data, response.data)
        self.assertNotIn(serializer2.data, response.data)

    def test_filter_profile_by_birth_date(self):
        response = self.client.get(PROFILE_URL, {"birth_date": "2001-01-01"})

        serializer1 = ProfileListSerializer(self.profile1)
        serializer2 = ProfileListSerializer(self.profile2)

        self.assertIn(serializer1.data, response.data)
        self.assertNotIn(serializer2.data, response.data)

    def test_retrieve_profile_detail(self):
        url = reverse("social_network:profile-detail", args=[self.profile1.id])
        res = self.client.get(url)
        serializer = ProfileSerializer(self.profile1)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_upload_image_to_profile(self):
        url = reverse("social_network:profile-upload-image", args=[self.profile1.id])
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")
        self.profile1.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.profile1.image.path))

    def test_follow_profile_action(self):
        url = profile_follow_or_unfollow_url(self.profile2.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"], f"Now you are following user {self.profile2}."
        )
        self.assertTrue(
            self.user1.profile.following.filter(id=self.profile2.id).exists()
        )

    def test_follow_self_profile_action(self):
        url = profile_follow_or_unfollow_url(self.profile1.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"], "You cannot follow/unfollow yourself."
        )

    def test_unfollow_profile_action(self):
        url = profile_follow_or_unfollow_url(self.profile2.id)
        self.client.get(url)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"],
            f"Now you are unfollowing user {self.profile2}.",
        )
        self.assertFalse(
            self.user1.profile.following.filter(id=self.profile2.id).exists()
        )

    def test_following_list_profile_action(self):
        for prof_id in (self.profile2.id, self.profile3.id):
            url = profile_follow_or_unfollow_url(prof_id)
            self.client.get(url)

        pofile_following_url = reverse("social_network:profile-following")
        res = self.client.get(pofile_following_url)
        pofile_following = self.profile1.following.order_by("id")
        serializer = ProfileListSerializer(pofile_following, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_followers_list_profile_action(self):
        for user in (self.user2, self.user3):
            self.client.force_authenticate(user)
            url = profile_follow_or_unfollow_url(self.profile1.id)
            self.client.get(url)

        self.client.force_authenticate(self.user1)
        pofile_followers_url = reverse("social_network:profile-followers")
        res = self.client.get(pofile_followers_url)
        pofile_followers = self.profile1.followers.order_by("id")
        serializer = ProfileListSerializer(pofile_followers, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
