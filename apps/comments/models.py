from django.conf import settings
from django.db import models


class Comment(models.Model):
    """
    Model representing comment.

    Logic: (key moments)
        - Defines 'post' and 'author' as ForeignKeys to Post and User models.
          The 'related_name' attributes allow backward lookups like post.comments.all()
          and user.comments.all().
        - Implements cascade deletion: if an author or post is deleted,
          the related comments are automatically removed.
        - "parent" is a self-referential ForeignKey. A comment can be a reply to
          another comment. By setting null=True and blank=True, we allow
          top-level comments to exist without a parent.
        - Three composite indexes are used to boost database performance:
            1) Filter by post_id and order by newest first.
            2) Filter by author and order by newest first.
            3) Filter by parent and order by newest first.
        - The "replies_count" property returns the number of active replies to this comment.
        - The "is_reply" property returns True if the comment is a reply to another comment.
    """

    post = models.ForeignKey(
        "posts.Post", on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "comments"
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["post", "-created_at"]),
            models.Index(fields=["author", "-created_at"]),
            models.Index(fields=["parent", "-created_at"]),
        ]

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"

    @property
    def replies_count(self: "Comment"):
        return self.replies.filter(is_active=True).count()

    @property
    def is_reply(self):
        return self.parent is not None
