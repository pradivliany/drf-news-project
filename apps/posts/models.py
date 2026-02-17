from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    """
    Model representing post's category.

    Attributes:
        name: -> Unique name of the category. Required.
        slug: SlugField -> Unique URL identifier. Auto-generated if not provided.
        description -> Optional info about the category.
        created_at -> Timestamp when the category was created.
    Notice:
        SlugField ensures on DB level validation for URL-safe characters.
        save() method automates slug generation.
        ordering allows consistent API response.
    """

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "categories"
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Post(models.Model):
    """
    Model representing post. (core model)

    Logic: (key moments)
        - STATUS_CHOICES: Implements visibility logic. 'published' is for the public API,
          while 'draft' keeps content private for authors/staff.
        - SET_NULL for categories ensures that deleting a category won't wipe out posts content.
        - CASCADE on author is logical — if author is deleted, his personal posts are removed as well.
        - related_name="posts" allows clean reverse lookups like category.posts.all() or user.posts.all().
        - New posts are 'published' by default for immediate visibility.
        - Database Indexes boosts productivity: specifically indexed
          to speed up sorting by date, filtering by status, author, and category.
        - get_absolute_url() to provide human-readable URLs.
        - slugify() handles URL creation on save if not provided manually.

    Features:
        - increment_views(): Method for tracking popularity without full model saves.
        - comments_count: Property to show engagement level on the frontend.
    """

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    content = models.TextField()
    image = models.ImageField(upload_to="posts/", blank=True, null=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts"
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="published"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "posts"
        verbose_name = "Post"
        verbose_name_plural = "Posts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["category", "-created_at"]),
            models.Index(fields=["author", "-created_at"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("post-detail", kwargs={"slug": self.slug})

    @property
    def comments_count(self):
        return self.comments.filter(is_active=True).count()

    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=["views_count"])
