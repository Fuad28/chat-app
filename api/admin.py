from django.apps import apps
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from api.models.user import User


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("email", "first_name", "last_name", "is_active")
    list_filter = ("email", "first_name", "last_name", "is_active")
    fieldsets = (
        (None, {"fields": ("email",)}),
        ("Personal Info", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )
    search_fields = ("email", "name", "first_name", "last_name")
    ordering = ("email",)


admin.site.register(User, CustomUserAdmin)

class BaseModelMixinAdmin(admin.ModelAdmin):
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )


# for model in apps.get_app_config("api").get_models():
#     if (model != User) and (model != WalletTransaction):
#         admin.site.register(model, admin.ModelAdmin)
