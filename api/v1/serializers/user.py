from djoser.serializers import (
    UserSerializer as BaseUserSerializer, 
    UserCreateSerializer as BaseUserCreateSerializer,
    )

from api.models import User

class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        fields = ["id", "password", "email", "first_name", "last_name"]


class UserRetrieveSerializer(BaseUserSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "is_active"]