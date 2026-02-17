from django.utils.text import slugify
from rest_framework import serializers

from .models import Category, Post


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer representing Category model.

    Notes:
        - get_posts_count(obj): obj parameter is the Category instance.
          Thanks to the 'related_name="posts"' in the Post model.
        - posts_count: Custom SerializerMethodField that calculates the number of published posts.
        - "slug" is in read_only_fields to protect URL.
    """

    posts_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "posts_count", "created_at"]
        read_only_fields = ["slug", "created_at"]

    def get_posts_count(self, obj):
        return obj.posts.filter(status="published").count()

    # todo may delete this, cuz same work does save method in Category model.
    def create(self, validated_data):
        validated_data["slug"] = slugify(validated_data["name"])
        return super().create(validated_data)


class PostListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing posts (GET requests):

    Notes:
        - StringRelatedField(): Instead of returning a raw ID, it calls the __str__
          method of the related Category and User models. (output like "author: admin" instead of "author: 1")
        - ReadOnlyField(): DRF looks to the Post model and finds @property 'comments_count'.
          (doesn't require inclusion in Meta.read_only_fields)
        - to_representation(instance): This method acts as a post-processing hook. It takes the
          model instance, converts it to a standard Python dict via super(), and allows
          manual modification of the data before it's sent as JSON. Returns dict.
        - 'slug', 'author', 'views_count' are protected from being modified by clint.
    """

    author = serializers.StringRelatedField()
    category = serializers.StringRelatedField()
    comments_count = serializers.ReadOnlyField()

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "slug",
            "content",
            "image",
            "category",
            "author",
            "status",
            "created_at",
            "updated_at",
            "views_count",
            "comments_count",
        ]
        read_only_fields = ["slug", "author", "views_count"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if len(data["content"]) > 200:
            data["content"] = data["content"][:200] + "..."
        return data


class PostDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed post view (GET requests):

    Notes:
        - 'author_info', 'category_info' are SerializerMethodFields, retrieving not raw IDs, but full useful data.
        - if there is no category -> returns None.
        - 'comments_count' -> maps to model's @property.
    """

    author_info = serializers.SerializerMethodField()
    category_info = serializers.SerializerMethodField()
    comments_count = serializers.ReadOnlyField()

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "slug",
            "content",
            "image",
            "category",
            "category_info",
            "author",
            "author_info",
            "status",
            "created_at",
            "updated_at",
            "views_count",
            "comments_count",
        ]
        read_only_fields = ["slug", "author", "views_count"]

    def get_author_info(self, obj):
        author = obj.author
        return {
            "id": author.pk,
            "username": author.username,
            "full_name": author.full_name,
            "avatar": author.avatar.url if author.avatar else None,
        }

    def get_category_info(self, obj):
        if obj.category:
            category = obj.category
            return {"id": category.pk, "name": category.name, "slug": category.slug}
        return None


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating or updating posts (POST, PUT, PATCH):

    Notes:
        - fields: only basic data from client (title, content, image, category, status).
        - create(): automatically injects current user as 'author' from request context
          and generates 'slug' from title before saving.
        - update(): checks if 'title' is being changed. If yes -> regenerates 'slug'.
        - Returns results by calling super() methods to handle DB operations.
    """

    class Meta:
        model = Post
        fields = ["title", "content", "image", "category", "status"]

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        validated_data["slug"] = slugify(validated_data["title"])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "title" in validated_data:
            validated_data["slug"] = slugify(validated_data["title"])
        return super().update(instance, validated_data)
