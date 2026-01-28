# Sets admin panel to work with our models.

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin interface for the User model.

    Attributes:
        list_display: list -> Fields shown in the users list table.
        list_filter: list -> Filters available in the right sidebar.
        search_fields: list -> Fields used by the search bar to find users.
        ordering: list -> Sorting order for the users list.
        fieldsets: list -> Organization for the user's edit page. (tuples of double elements)
        add_fieldsets: list -> Organization for the user's creating page.
        readonly_fields -> Fields that are visible but not editable. (timestamps)

    Notice: class "wide" is build-in Django Admin panel via CSS. (makes field as wide as possible)
    """

    list_display = [
        "email",
        "username",
        "first_name",
        "last_name",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "is_staff", "is_superuser", "created_at"]
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering = [
        "-created_at",
    ]
    fieldsets = [
        (None, {"fields": ["email", "username", "password"]}),
        ("Personal Info", {"fields": ["first_name", "last_name", "avatar", "bio"]}),
        (
            "Permissions",
            {
                "fields": [
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ]
            },
        ),
        (
            "Important dates",
            {"fields": ["last_login", "date_joined", "created_at", "updated_at"]},
        ),
    ]
    add_fieldsets = [
        (
            None,
            {
                "classes": [
                    "wide",
                ],
                "fields": ["email", "username", "password1", "password2"],
            },
        )
    ]
    readonly_fields = ["created_at", "updated_at", "date_joined", "last_login"]


# We can use -> admin.site.register(User, UserAdmin) if not decorator.
