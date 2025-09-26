from rest_framework import permissions, exceptions, status
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken


class IsAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        try:
            outstanding_tokens = OutstandingToken.objects.filter(user=request.user.id)
            for token in outstanding_tokens:
                if BlacklistedToken.objects.filter(token=token).exists():
                    raise exceptions.NotAuthenticated('Login qiling!')
            return True

        except OutstandingToken.DoesNotExist:
            raise exceptions.NotFound("Token not found!")
