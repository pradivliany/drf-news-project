from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model:
    blank=True -> allows lo leave an empty field in form.
    null=True -> avatar field in db needs to have either Path to file or NULL.
    is_active field -> to protect consistency of data. Or to disallow user write comments etc.
    USERNAME_FIELD -> email is now unique identifier for the User.
    db_table -> renames table from  "accounts_users" to "users".
    verbose_name -> model's readable name in Admin panel.
    @property -> turns method to attribute (user.full_name and NOT user.full_name()).
    """

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
