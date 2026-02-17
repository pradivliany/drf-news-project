from django.contrib import admin

from .models import Category, Post


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Category model.

    Notes:
        - slug is automatically generated via name.
        - displaying the total number op posts in each category.
    """

    list_display = ["name", "slug", "posts_count", "created_at"]
    list_filter = [
        "created_at",
    ]
    search_fields = ["name", "description"]
    prepopulated_fields = {
        "slug": [
            "name",
        ]
    }
    readonly_fields = [
        "created_at",
    ]

    @admin.display(description="Posts count")
    def posts_count(self, obj):
        """Returns the number of posts related to this category."""
        return obj.posts.count()


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """
    Admin configuration for Post model.

    Notes:
        - slug is automatically generated via title.
        - for performance using select_related (author, category).
        - Statistics tracking (views and comment counts).
    """

    list_display = [
        "title",
        "author",
        "category",
        "status",
        "views_count",
        "comments_count",
        "created_at",
    ]
    list_filter = ["status", "category", "created_at", "updated_at"]
    search_fields = ["title", "content", "author__username"]
    prepopulated_fields = {
        "slug": [
            "title",
        ]
    }
    readonly_fields = ["created_at", "updated_at", "views_count"]
    raw_id_fields = [
        "author",
    ]

    fieldsets = [
        (None, {"fields": ["title", "slug", "content", "image"]}),
        ("Meta", {"fields": ["category", "author", "status"]}),
        (
            "Statistics",
            {
                "fields": ["views_count", "created_at", "updated_at"],
                "classes": [
                    "collapse",
                ],
            },
        ),
    ]

    @admin.display(description="Comments")
    def comments_count(self, obj):
        """Returns the total number of comments for the post."""
        return obj.comments.count()

    def get_queryset(self, request):
        """Optimizing queries by pre-fetching related author and category."""
        return super().get_queryset(request).select_related("author", "category")
