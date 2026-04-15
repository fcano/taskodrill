from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Object-level permission: only the owner (obj.user == request.user)
    may read or mutate the object.
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
