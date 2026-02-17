from django.contrib import admin

from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Comment model.

    Notes:
        - list_display: Columns visible in the table. Uses methods for related data & previews.
        - list_filter: Right-side panel for quick filtering by status and dates.
        - search_fields: Search bar logic. Supports '__' for relational lookups (author/post).
        - readonly_fields: Protects auto-generated timestamps from manual editing.
        - raw_id_fields: Replaces heavy dropdowns with lightweight ID inputs + lookup window.
        - list_editable: Enables instant status toggling directly from the list view.
        - fieldsets: Groups fields into logical sections on the edit page (with collapse effect).
        - get_queryset: Optimization to prevent N+1 queries using select_related.
        - actions: Bulk operations to activate/deactivate multiple comments at once.
    """

    list_display = [
        "id",
        "post_title",
        "author",
        "content_preview",
        "parent_comment",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "created_at", "updated_at"]
    search_fields = ["content", "author__username", "post__title"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["author", "post", "parent"]
    list_editable = [
        "is_active",
    ]
    fieldsets = [
        (None, {"fields": ["post", "author", "parent", "content"]}),
        (
            "Status",
            {
                "fields": [
                    "is_active",
                ]
            },
        ),
        (
            "Timestamps",
            {
                "fields": ["created_at", "updated_at"],
                "classes": [
                    "collapse",
                ],
            },
        ),
    ]

    @admin.display(description="Post")
    def post_title(self, obj):
        return obj.post.title

    @admin.display(description="Content Preview")
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    @admin.display(description="Parent")
    def parent_comment(self, obj):
        if obj.parent:
            return f"Reply to: {obj.parent.content[:30]}..."
        return "Main comment"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("author", "post", "parent")

    actions = ["make_active", "make_inactive"]

    @admin.action(description="Mark selected comments as active")
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} comments were marked as active.")

    @admin.action(description="Mark selected comments as inactive.")
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} comments were marked as inactive.")
