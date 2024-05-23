from django.urls import path
from rest_framework_nested import routers
from rest_framework_simplejwt import views as simple_jwt_views

from api.v1.views import UserViewSet, ConversationViewSet


app_name = "api-v1"

router = routers.DefaultRouter()
router.register("bank-accounts", ConversationViewSet, basename= "conversation-view")

urlpatterns = [

    #auth
    path("login/", simple_jwt_views.TokenObtainPairView.as_view(), name="login"),
    path("refresh/", simple_jwt_views.TokenRefreshView.as_view(), name="refresh-token"),
    path("verify/", simple_jwt_views.TokenVerifyView.as_view(), name="verify-token"),
    path("users/", UserViewSet.as_view({"post": "create", "get": "list"}), name="users"),
    path("me/", UserViewSet.as_view({"get": "me", "delete": "me", "patch": "me", "put": "me"})),
    path("forgot-password/", UserViewSet.as_view({"post": "reset_password"}), name="forgot-password"),
    path("forgot-password-confirm/", UserViewSet.as_view({"post": "reset_password_confirm"}), name="forgot-password-confirm"),
    path("reset-password/", UserViewSet.as_view({"post": "set_password"}), name="reset-password"),
    
    ] + router.urls
