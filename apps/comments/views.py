from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.posts.models import Post

from .models import Comment
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    CommentCreateSerializer,
    CommentDetailSerializer,
    CommentSerializer,
    CommentUpdateSerializer,
)


class CommentListCreateView(generics.ListCreateAPIView):
    """
    API view for listing comments (GET) and creating new ones (POST).

    Notes:
        - Serializer: Uses CommentSerializer for listings and CommentCreateSerializer for creation.
        - Permissions: IsAuthenticatedOrReadOnly ensures only logged-in users can post.
        - Optimization: Uses select_related in get_queryset to minimize database hits.
        - Filtering: Supports filtering by post, author, and parent via DjangoFilterBackend.
        - Search: Allows text-based search within the 'content' field.
        - Ordering: Default sorting is by newest comments (-created_at).

    POST Request Flow:
        1. Request reaches the view.
        2. get_serializer_class() switches to CommentCreateSerializer.
        3. Serializer runs validate_post (checks if published) and validate (checks parent-post link).
        4. Serializer's create() method injects the current user as the author.
        5. A new Comment instance is saved to the DB and returned to the frontend.
    """

    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["post", "author", "parent"]
    search_fields = ["content"]
    ordering_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Comment.objects.filter(is_active=True).select_related(
            "author", "post", "parent"
        )

    def get_serializer_class(self):
        match self.request.method:
            case "POST":
                return CommentCreateSerializer
            case _:
                return super().get_serializer_class()


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving (GET), updating (PUT/PATCH), or deleting (DELETE) a specific comment.

    Notes:
        - Queryset: Filters active comments and uses select_related for performance.
        - Serializers: Switches between Detail and Update serializers based on the HTTP method.
        - Permissions: Anyone can view; only the author can modify or delete (IsAuthorOrReadOnly).

    Method Flow:
        - GET (Retrieve): Passes the found object through CommentDetailSerializer.
          Returns full data, including nested replies.

        - PUT/PATCH (Update): Switches to CommentUpdateSerializer to restrict editable fields.
          Checks authorship before applying changes and returning the updated object.

        - DELETE (Destroy): DRF locates the object and calls perform_destroy().
          Executes a 'soft delete' (is_active=False). The object remains in the DB
          but becomes invisible to the API. Returns HTTP 204 No Content.
    """

    queryset = Comment.objects.filter(is_active=True).select_related("author", "post")
    serializer_class = CommentDetailSerializer
    permission_classes = [IsAuthorOrReadOnly]

    def get_serializer_class(self):
        match self.request.method:
            case "PUT" | "PATCH":
                return CommentUpdateSerializer
            case _:
                return super().get_serializer_class()

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class MyCommentsView(generics.ListAPIView):
    """
    API view to retrieve a list of comments created by the currently authenticated user.

    Notes:
        - Permissions: Only authenticated users can access this endpoint.
        - Serializer: Uses CommentSerializer to display basic comment data.
        - Filtering: Filter by post, parent, or status.
            * Example: ?post=5 (only comments for post ID 5)
            * Example: ?is_active=false (view your soft-deleted comments)
        - Search: Text-based search in 'content' field.
            * Example: ?search=python (find comments containing 'python')
        - Ordering: Sort by creation or update time.
            * Default: ?ordering=-created_at (newest first)
            * Example: ?ordering=created_at (oldest first)
            * Example: ?ordering=-updated_at (recently edited first)
    """

    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["post", "parent", "is_active"]
    search_fields = ["content"]
    ordering_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Comment.objects.filter(author=self.request.user).select_related(
            "post", "parent"
        )


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def post_comments(request, post_id):
    """
    Retrieves a structured list of comments for a specific published post.

    Flow:
        1. URL provides 'post_id' -> Fetch the post from DB (ensure it's 'published' or 404).
        2. Complex Database Query:
           - Filter: Get only 'is_active' comments for this post that have NO parent (root comments).
           - select_related('author'): Joins the User table to get root comment authors immediately.
           - prefetch_related('replies__author'): Executes a second optimized query to fetch
             ALL child comments AND their authors in one go.
        3. Sorting: Newest root comments first (-created_at).

    Response Structure:
        a) post: Basic info (id, title, slug) of the target post.
        b) comments: The full tree (Root -> Replies) processed through CommentDetailSerializer.
        c) comments_count: Total number of active comments (both root and replies).
    """

    post = get_object_or_404(Post, pk=post_id, status="published")

    # to get only main comments
    comments = (
        Comment.objects.filter(post=post, parent=None, is_active=True)
        .select_related("author")
        .prefetch_related("replies__author")
        .order_by("-created_at")
    )

    serializer = CommentDetailSerializer(
        comments, many=True, context={"request": request}
    )
    return Response(
        {
            "post": {"id": post.pk, "title": post.title, "slug": post.slug},
            "comments": serializer.data,
            "comments_count": post.comments.filter(is_active=True).count(),
        }
    )


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def comment_replies(request, comment_id):
    """
    API view to retrieve all active replies to a specific comment.

    Flow:
        1. Get the parent comment by ID. If it's inactive or doesn't exist -> 404.
        2. Database Request:
           - Filter: Get all comments where 'parent' is our comment_id and 'is_active' is True.
           - select_related('author'): Efficiently fetch info about who wrote each reply.
           - Sorting: Oldest first (created_at) to maintain conversation flow.
        3. Serialization: Process both parent and child comments to return full data.

    URL Example:
        /api/comments/15/replies/ -> returns all replies for comment #15.
    """

    parent_comment = get_object_or_404(Comment, pk=comment_id, is_active=True)

    replies = (
        Comment.objects.filter(parent=parent_comment, is_active=True)
        .select_related("author")
        .order_by("created_at")
    )
    serializer = CommentSerializer(replies, many=True, context={"request": request})
    return Response(
        {
            "parent_comment": CommentSerializer(
                parent_comment, context={"request": request}
            ).data,
            "replies": serializer.data,
            "replies_count": replies.count(),
        }
    )
