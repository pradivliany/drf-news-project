from rest_framework import serializers

from apps.posts.models import Post

from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    """
    Base Comment Serializer (GET).
    (used to display the list of comments for a specific post.)

    Notes:
        - returns basic comment fields defined in Meta.fields.
        - author_info: SerializerMethodField calculated on the fly.
        - replies_count: displays only the total count of replies, not the objects themselves.
    """

    author_info = serializers.SerializerMethodField()
    replies_count = serializers.ReadOnlyField()
    is_reply = serializers.ReadOnlyField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "content",
            "author",
            "author_info",
            "parent",
            "is_active",
            "replies_count",
            "is_reply",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["author", "is_active"]

    def get_author_info(self, obj):
        return {
            "id": obj.author.id,
            "username": obj.author.username,
            "fullname": obj.author.full_name,
            "avatar": obj.author.avatar.url if obj.author.avatar else None,
        }


class CommentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer exclusively for creating new comments (POST).

    Notes:
        - Required fields: post (ID), content (text), and parent (ID, optional).
        - validate_post: ensures the post exists and is currently 'published'.
        - validate: cross-checks that the parent comment belongs to the same post.
        - create: automatically injects the authenticated user as the author.
    """

    class Meta:
        model = Comment
        fields = ["post", "parent", "content"]

    def validate_post(self, value):
        if not Post.objects.filter(id=value.id, status="published").exists():
            raise serializers.ValidationError("Post not found.")
        return value

    def validate_parent(self, value):
        if value and value.post != self.initial_data.get("post"):
            raise serializers.ValidationError(
                "Parent comment must belong to the same post."
            )
        return value

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        return super().create(validated_data)


class CommentUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating existing comments (PUT | PATCH).

    Notes:
        - Only the 'content' field is allowed to be modified.
        - Prevents users from changing the post, parent, or author after creation.
    """

    class Meta:
        model = Comment
        fields = ["content"]


class CommentDetailSerializer(CommentSerializer):
    """
    Serializer for detailed comment view, including nested replies.

    Notes:
        - Inherits from CommentSerializer for DRY.
        - "replies" is a SerializerMethodField that fetches child comments.
        - To prevent deep recursion, replies are only fetched for top-level comments
          (where parent is None).
    """

    replies = serializers.SerializerMethodField()

    class Meta(CommentSerializer.Meta):
        fields = CommentSerializer.Meta.fields + ["replies"]

    def get_replies(self, obj):
        if obj.parent is None:
            replies = obj.replies.filter(is_active=True).order_by("created_at")
            return CommentSerializer(replies, many=True, context=self.context).data
        return []
