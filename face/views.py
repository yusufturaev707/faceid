from rest_framework import viewsets, permissions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import authenticate, login

from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from tutorial.quickstart.serializers import UserSerializer
from face.face_embedder import FaceEmbedder
from users.models import User

class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        try:
            username = request.data.get('username')
            password = request.data.get('password')

            user = authenticate(username=username, password=password)

            if user is not None:
                user = User.objects.get(username=username)
                if user.is_blocked:
                    data = {
                        "success": False,
                        "message": "Sorry, blocked by Admin",
                        "result": {
                            "access_token": "",
                            "user": {
                                "id": user.id,
                                "username": user.username,
                                "is_blocked": user.is_blocked,
                            }
                        }
                    }
                    return Response(data, status=status.HTTP_423_LOCKED)

                refresh = RefreshToken.for_user(user)
                login(request, user)
                token_users = OutstandingToken.objects.filter(user=user).order_by('id')
                token_user = token_users.last()

                response = {
                    "success": True,
                    "message": "Success",
                    "result": {
                        "refresh_token": str(refresh),
                        "access_token": str(refresh.access_token),
                        "user": {
                            "id": token_user.user.id,
                            "username": token_user.user.username,
                            "is_blocked": token_user.user.is_blocked,
                            "region": {
                                "name": token_user.user.region.name if user.region else "",
                                "number": token_user.user.region.number if user.region else 0,
                            },
                        }
                    }
                }
                return Response(response, status=status.HTTP_200_OK)
            else:
                response = {
                    "success": False,
                    "message": "Kechirasiz tizimdan topilmadingiz!",
                    "result": {}
                }
                return Response(response, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.all().order_by('id')


class StudentViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication, TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.all().order_by('id')

    @action(methods=['post'], detail=False)
    def one_to_one_compare_face(self, request):
        try:
            first_image = str(request.data['first_image'])
            second_image = str(request.data['second_image'])

            face_embedder = FaceEmbedder()

            if not face_embedder.validate_base64(first_image):
                raise Exception("Invalid Base64 string. Must start with a valid image data URI prefix.")

            if not face_embedder.validate_base64(second_image):
                raise Exception("Invalid Base64 string. Must start with a valid image data URI prefix.")

            img_rgb_1 = face_embedder.decode_base64(first_image)
            embedding_1 = face_embedder.get_embedding(img_rgb_1)

            img_rgb_2 = face_embedder.decode_base64(second_image)
            embedding_2 = face_embedder.get_embedding(img_rgb_2)

            similarity = face_embedder.compare_faces(embedding_1, embedding_2)

            if similarity >= 40:
                data = {"status": status.HTTP_200_OK, "score": f"{similarity}%", "verified": True,
                        "message": "Aniqlandi"}
                return Response(data=data, status=status.HTTP_200_OK)
            else:
                data = {"status": status.HTTP_404_NOT_FOUND, "score": f"{similarity}%", "verified": False,
                        "message": "Topilmadi"}
                return Response(data=data, status=status.HTTP_200_OK)
        except Exception as e:
            data = {"status": status.HTTP_500_INTERNAL_SERVER_ERROR, "message": f"{e}"}
            return Response(data, status=status.HTTP_200_OK)