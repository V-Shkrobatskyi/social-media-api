from rest_framework import routers

from social_network.views import (
    ProfileViewSet,
    PostViewSet,
    CommentViewSet,
    LikeViewSet,
)

app_name = "social_network"

router = routers.DefaultRouter()
router.register("profiles", ProfileViewSet)
router.register("posts", PostViewSet)
router.register("comments", CommentViewSet)
router.register("likes", LikeViewSet)

urlpatterns = router.urls
