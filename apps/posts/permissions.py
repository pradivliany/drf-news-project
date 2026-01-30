from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj) -> bool:
        """
        Object-level permission to only allow authors of the object to edit it.

        P.S. Works ONLY for retrieve, update, partial_update and destroy. (where 'obj' exists)

        - request: holds request.user, method (GET, DELETE, etc.).
        - view: the specific ViewSet handling the logic.
        - obj: the model instance (e.g., Post with id=5).

        Flow: (for example DELETE /api/posts/5)
        1) URL -> View -> get_object()
        2) Permissions:
            - has_permission: global check. (e.g., if user logged in?)
            - has_object_permission: specific check for Post #5.
        3) return bool. (compares obj.author with request.user)
        """

        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user
