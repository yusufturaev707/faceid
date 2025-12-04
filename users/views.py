import time

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate, login

from users.models import User


class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def post(request):
        try:
            username, password = request.data.get('username'), request.data.get('password')
            user = authenticate(username=username, password=password)

            if not user:
                return Response({"success": False, "message": "Kechirasiz tizimdan topilmadingiz!", "result": {}},
                                status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.filter(username=username).first()

            if not user.is_active:
                return Response({"success": False, "message": "Sorry, blocked by Admin",
                                 "result": {"refresh_token": "", "access_token": "",
                                            "user": {"id": user.id, "username": user.username,
                                                     "is_active": user.is_active}}}, status=status.HTTP_423_LOCKED)

            # Eski tokenlarni o'chirish
            OutstandingToken.objects.filter(user=user).delete()
            refresh = RefreshToken.for_user(user)

            return Response({"success": True, "message": "Success",
                             "result": {
                                 "refresh_token": str(refresh),
                                 "access_token": str(refresh.access_token),
                                 "token_type": "Bearer",
                                 "user": {
                                     "id": user.id,
                                     "username": user.username,
                                     "is_active": user.is_active
                                 }
                             }}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e), "result": {}},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CustomTokenRefreshView(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def post(request):
        try:
            refresh_token = request.data.get('refresh_token')

            if not refresh_token:
                return Response(
                    {"success": False, "message": "Refresh token talab qilinadi", "result": {}},
                    status=status.HTTP_400_BAD_REQUEST
                )

            refresh = RefreshToken(refresh_token)

            # Refresh token muddatini tekshirish
            if refresh.get('exp') < time.time():
                return Response(
                    {"success": False, "message": "Refresh token muddati tugagan", "result": {}},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Yangi access token yaratish
            new_access_token = str(refresh.access_token)

            return Response({
                "success": True,
                "message": "Token muvaffaqiyatli yangilandi",
                "result": {
                    "access_token": new_access_token,
                    "refresh_token": str(refresh)  # Yangi refresh token ham berish mumkin
                }
            }, status=status.HTTP_200_OK)

        except TokenError as e:
            return Response(
                {"success": False, "message": "Refresh token yaroqsiz", "result": {}},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {"success": False, "message": str(e), "result": {}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LogoutView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response(
                {"status": False, "message": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {"status": False, "message": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"status": True, "message": "Successfully logged out."},
            status=status.HTTP_200_OK
        )