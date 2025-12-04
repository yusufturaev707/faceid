from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from supervisor.serializers import SupervisorSerializer, EventSupervisorSerializer


class SupervisorCreateView(APIView):
    def post(self, request):
        serializer = SupervisorSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': "Nazoratchi muvaffaqiyatli qo'shildi",
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'success': False,
            'message': 'Ma\'lumotlar noto\'g\'ri',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)



class EventSupervisorCreateView(APIView):
    def post(self, request):
        serializer = EventSupervisorSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': "Testga nazoratchi muvaffaqiyatli qo'shildi",
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'success': False,
            'message': 'Ma\'lumotlar noto\'g\'ri',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
