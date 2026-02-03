from django.db.models import Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import Category, Post
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    CategorySerializer,
    PostCreateUpdateSerializer,
    PostDetailSerializer,
    PostListSerializer,
)


class CategoryListCreateView(generics.ListCreateAPIView):
    """
    View for listing categories or creating a new one:

    Notes:
        - generics.ListCreateAPIView: pre-built view for GET (list) and POST (create) methods.
        - queryset: defines the base collection of Category objects for this view.
        - serializer_class: the 'translator' between JSON and Category model instances
        - permissions: IsAuthenticatedOrReadOnly — unrestricted GET, restricted POST.
        - filter_backends: provides tools for frontend to filter/sort data via URL params.
        - search_fields: enables text search (?search=) across name and description.
        - ordering_fields: list of fields client is allowed to sort by.
        - ordering: default sort order if no ?ordering= parameter is provided.

    Flow: (example GET /api/categories/?search=python)
    1) Permissions: check if GET is allowed
    2) Queryset: fetch all categories from the database.
    3) FilterBackends: apply SearchFilter (looking for 'python' in name/description)
    4) Ordering: apply default 'name' sort to the filtered results.
    5) Serializer: pass filtered categories through CategorySerializer (e.g., to get posts_count).
    6) Response: send the final JSON data to the client.
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View to GET (retrieve), PATCH/PUT (update) or DELETE specific category:

    Notes:
        - queryset: defines the "pool" of objects where DRF search is allowed.
        - lookup_field: tells DRF to use the 'slug' from the URL to find the specific record in the DB.

    Flow: (example PATCH /api/categories/news/ with data {"description": "New description"})
    1) URL matching: routing finds this view based on the URL pattern.
    2) lookup: DRF identifies "news" as the 'slug' parameter from the URL.
    3) Get Object: built-in get_object() method executes Category.objects.all().get(slug="news").
    4) Permissions: because PATCH is not safe method -> requires user to be authenticated.
    5) Validation: input data goes though CategorySerializer.
    6) Update: DRF updates data in the database.
    5) Serialization: again updated object goes through serializer with performed posts_count method.
    6) Response: returns the final JSON data of the updated object to the client.
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "slug"


class PostListCreateView(generics.ListCreateAPIView):
    """
    View for listing posts or creating a new one: (GET, POST)

    Notes:
        - select_related: used for Many-to-One relationships (author, category).
          Performs an SQL JOIN to fetch related data in a single query, preventing the N+1 problem.
        - Q objects: allow complex lookups using OR (|), AND (&), and NOT (~).
          Used here to show posts that are either "published" OR owned by the current user.
        - DjangoFilterBackend: allows exact filtering via URL parameters (e.g., ?category=1).
        - get_serializer_class: dynamically switches to PostCreateUpdateSerializer for POST requests.

    Flow GET: (example: /api/posts/?category=2)
    1) Permissions: IsAuthenticatedOrReadOnly allows GET for everyone
    2) get_queryset: applies select_related and filters data based on user authentication (Q objects).
    3) Filtering: DjangoFilterBackend adds "WHERE category_id = 2" to the SQL query.
    4) Ordering: applies "-created_at" as the default sorting.
    5) Serialization: uses PostListSerializer to return a list of posts.
    """

    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category", "author", "status"]
    search_fields = ["title", "content"]
    ordering_fields = [
        "created_at",
        "updated_at",
        "views_count",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = Post.objects.select_related("author", "category")
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(status="published")
        else:
            queryset = queryset.filter(
                Q(status="published") | Q(author=self.request.user)
            )

        return queryset

    def get_serializer_class(self):
        match self.request.method:
            case "POST":
                return PostCreateUpdateSerializer
            case _:
                return super().get_serializer_class()


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View to retrieve(GET), update(PUT, PATCH) or delete a specific post:

    Notes:
        - select_related: optimization the query by JOINing "category" and "author" tables.
        - lookup_field: tells DRF to use "slug" from URL to identify post.
        - IsAuthorOrReadOnly: custom permission allows only the author to edit | delete.
        - retrieve: overriding method managing GET requests to increase views_count field.

    Flow GET: (example: /api/posts/my-cool-post/)
    1) Lookup: identifies the post by slug.
    2) Custom permission: returns True, because GET is safe method.
    3) retrieve method: increases views_count.
    4) serializer: for converting to JSON.
    5) returns updated post data.
    """

    serializer_class = PostDetailSerializer
    permission_classes = [IsAuthorOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        queryset = Post.objects.select_related("category", "author")
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(status="published")
        else:
            queryset = queryset.filter(
                Q(status="published") | Q(author=self.request.user)
            )
        return queryset

    def get_serializer_class(self):
        match self.request.method:
            case "PUT" | "PATCH":
                return PostCreateUpdateSerializer
            case _:
                return super().get_serializer_class()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.increment_views()
        serializer = self.get_serializer(instance)

        return Response(serializer.data)


class MyPostsView(generics.ListAPIView):
    """
    View to list all posts belonging to currently authenticated user:

    Notes:
        - permission_classes were not necessary to put here, global settings says the same.
        - Filtering: Supports filtering by category/status, searching title/content, and various ordering options.

    Flow GET (example: /api/my-posts/?status=draft):
    1) Permissions: DRF checks if the user is logged in. If not -> 401 Unauthorized.
    2) get_queryset: Executes Post.objects.filter(author=current_user).
    3) FilterBackend: Adds 'AND status = draft' to the SQL query.
    4) Serialization: Uses PostListSerializer to return the user's personal list.
    """

    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category", "status"]
    search_fields = ["title", "content"]
    ordering_fields = ["created_at", "updated_at", "views_count", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user).select_related(
            "category", "author"
        )


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def post_by_category(request, category_slug):
    """
    Function-based view to retrieve all published posts belonging to a specific category:

    Notes:
        - @api_view(["GET"]): restricts the endpoint to GET requests only (returns 405 for others).
        - AllowAny: makes this endpoint public so anyone can browse categories.
        - context={"request": request}: explicitly passed to the serializer to ensure absolute URLs
          for image fields (e.g., http://localhost:8000/media/path.jpg instead of just /media/path.jpg)

    Flow:
    1) Lookup: get_object_or_404 finds the category by slug or 404 error.
    2) Queryset: fetches posts linked to this category with status="published".
    3) Uses select_related to join author and category tables in one SQL query.
    4) Serialization: converts both the category object and the posts list into JSON.
    5) Result: returns a structured response.
    """

    category = get_object_or_404(Category, slug=category_slug)
    posts = (
        Post.objects.filter(category=category, status="published")
        .select_related("category", "author")
        .order_by("-created_at")
    )
    serializer = PostListSerializer(posts, many=True, context={"request": request})
    return Response(
        {"category": CategorySerializer(category).data, "posts": serializer.data}
    )


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def popular_posts(request):
    """
    Endpoint to retrieve the top 10 most viewed published posts:

    Notes:
        - Security: only "published" posts are included.
        - Performance: uses [:10] -> SQL LIMIT 10.
        - Uses select_related to join author and category tables in one SQL query.
        - Ordering: uses "-views_count" to sort by popularity in descending order.

    Flow:
    1) Query: filters published posts and orders them by views_count (highest first).
    2) Limit: restricts the result to the top 10 items.
    3) Serialize: converts the queryset into JSON.
    4) Response: returns a simple list of 10 trending posts.
    """

    posts = (
        Post.objects.filter(status="published")
        .select_related("category", "author")
        .order_by("-views_count")[:10]
    )
    serializer = PostListSerializer(posts, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def recent_posts(request):
    """
    Endpoint to retrieve the 10 most recently published posts:

    Flow:
    1) Query: filters only "published".
    2) Sort: orders by "created_at" in descending order (newest first).
    3) Limit: slices the queryset to the first 10 items (SQL LIMIT 10).
    4) Serialize: converts the limited queryset into a JSON list.
    5) Response: returns the list of latest posts.
    """
    posts = (
        Post.objects.filter(status="published")
        .select_related("category", "author")
        .order_by("-created_at")[:10]
    )
    serializer = PostListSerializer(posts, many=True, context={"request": request})
    return Response(serializer.data)
