from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrReadOnly(BasePermission):
    """
    Permission class to ensure only the author can modify an object.

    Global vs Object Permission Logic:
        - has_permission: Checks general access before the view retrieves objects from the DB.
          (e.g., IsAuthenticated checks if the user is even allowed to enter).
        - has_object_permission: Runs after the object is retrieved from the DB.
          Checks specific access rules: Is the user the owner? Do they have access to this row?
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if the user has permission to perform a specific action on the object.

        :param request: The incoming Web request containing method, user, and context.
        :param view: The specific view handling the endpoint logic.
        :param obj: The model instance retrieved from the database.
        :return: bool (True if access is granted, False otherwise).
        """
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user
