from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer to register users:

    1) Serializer picks keys from JSON based on Meta.fields.
    2) Field-level Validation:
        a) Validates email format and uniqueness.
        b) Password validates by complex Django validators.
        c) write_only=True -> sensitive data will not be in API response.
    3) validate method ->
        a) attrs is dictionary of already validated fields.
        b) if passwords don't match -> raises ValidationError.
    4) create method ->
        a) Removes "password_confirm", as it is not in DB.
        b) Creates user from validated data with hashed password.
    5) serializer response ->
        a) New user object is being filtered through Meta.fields.
        b) Skips write_only fields, returning only public data. (username, email, names)
    """

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password": "Password fields did not match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer to log in user:

    1) Serializer picks keys from JSON (expects "email" and "password").
    2) Field-level Validation:
        a) Validates email format.
    3) validate method ->
        a) Gets email and password from attrs.
        b) Tries to authenticate user.
        c) Raises ValidationErrors if something is wrong on the way.
        d) Adds user object to attrs and returns it.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(
                request=self.context.get("request"), username=email, password=password
            )
            if not user:
                raise serializers.ValidationError("User not found.")
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled.")
            attrs["user"] = user
            return attrs
        else:
            raise serializers.ValidationError("Must include 'email' and 'password'.")


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user's profile:

    ReadOnlyField() -> takes result from @property and adds it in JSON.
    SerializerMethodField() -> says there are no data in model, and data will be counted in method below.
    read_only_fields -> says don't let user change them. (id, and DateTimeFields)

    Serialization Flow:
    1) View will get user from DB and puts him in this serializer.
    2) DRF will take most of the fields from user attributes.
    3) Serializer will call full_name in our model and inputs result.
    4) get_posts_count() and get_comments_count() will be called for user.
    5) Result dict will be used later in view as serializer.data.
    """

    full_name = serializers.ReadOnlyField()
    posts_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "avatar",
            "bio",
            "created_at",
            "updated_at",
            "posts_count",
            "comments_count",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_posts_count(self, obj):
        """Safely retrieving posts count"""
        try:
            return obj.posts.count()
        except AttributeError:
            return 0

    def get_comments_count(self, obj):
        """Safely retrieving comments count"""
        try:
            return obj.comments.count()
        except AttributeError:
            return 0


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serialization Flow:
    1) View finds the User object and passes it as "instance".
    2) Only Meta.fields allowed to be changed.
    3) 'setattr' dynamically updates each attribute of the 'instance' in memory.
    4) 'instance.save()' commits all changes to the Database (SQL UPDATE).
    5) Updated instance is returned back to the View.
    """

    class Meta:
        model = User
        fields = ["first_name", "last_name", "avatar", "bio"]

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serialization Flow:
    1) View gives us user from Context request.user.
    2) Runs validate_old_password firstly.
    3) Runs validate to ensure identicality of passwords.
    4) Save method hashes password, connects it with user in memory and finally saves it.
    """

    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True, write_only=True, validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password": "Password fields did not match."}
            )
        return attrs

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user
