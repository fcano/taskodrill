from django.contrib.auth import authenticate
from rest_framework import serializers, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, inline_serializer


class ObtainTokenView(APIView):
    """Exchange username + password for an API token."""
    permission_classes = [AllowAny]
    throttle_scope = 'login'

    @extend_schema(
        request=inline_serializer(
            name='TokenObtainRequest',
            fields={
                'username': serializers.CharField(),
                'password': serializers.CharField(),
            },
        ),
        responses={
            200: inline_serializer(
                name='TokenObtainResponse',
                fields={
                    'token': serializers.CharField(),
                    'user_id': serializers.IntegerField(),
                    'username': serializers.CharField(),
                },
            ),
            400: inline_serializer(
                name='TokenObtainError400',
                fields={'error': serializers.CharField()},
            ),
            401: inline_serializer(
                name='TokenObtainError401',
                fields={'error': serializers.CharField()},
            ),
        },
        summary='Obtain authentication token',
        description='Exchange username and password for a long-lived API token.',
    )
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'Both username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request=request, username=username, password=password)
        if user is None:
            return Response(
                {'error': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token, _created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user_id': user.pk, 'username': user.username})


class RevokeTokenView(APIView):
    """Delete the current user's token, effectively logging them out."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={204: None},
        summary='Revoke authentication token',
        description='Delete the current token, logging the user out of the API.',
    )
    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
