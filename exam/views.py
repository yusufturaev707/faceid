from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView
from django.views.decorators.cache import cache_page

from django.db import transaction

from exam.models import Student, Exam
from exam.serializers import StudentSerializer, ExamSerializer
from users.models import User


class StudentPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 500

    def paginate_queryset(self, queryset, request, view=None):
        try:
            return super().paginate_queryset(queryset, request, view)
        except NotFound:
            return []

    def get_paginated_response(self, data):
        if not data:
            return Response({
                'count': 0,
                'next': None,
                'previous': None,
                'total_pages': 0,
                'current_page': 0,
                'results': []
            })
        next_url = self.get_next_link()
        previous_url = self.get_previous_link()

        return Response({
            'count': self.page.paginator.count,
            'next':  next_url,
            'previous': previous_url,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data
        })


@method_decorator(cache_page(60 * 1), name='get')
class StudentListView(ListAPIView):
    serializer_class = StudentSerializer
    authentication_classes = [JWTAuthentication, TokenAuthentication]
    pagination_class = StudentPagination

    def get_queryset(self, user=None):
        queryset = Student.objects.select_related('exam', 'zone').only(
            'id', 'first_name', 'last_name', 'imei', 'exam__test__name', 'zone__region__name',
        ).filter(zone=user.zone).order_by('id')

        exam_id = self.request.query_params.get('exam_id')
        if not exam_id:
            return queryset.filter(exam__status__key='session_ready').first()
        return queryset.filter(exam_id=exam_id, exam__status__key='session_ready')


    def list(self, request, *args, **kwargs):
        user = User.objects.get(pk=request.user.pk)
        queryset = self.filter_queryset(self.get_queryset(user))
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        response = self.get_paginated_response(serializer.data)
        return response


class ExamViewSet(viewsets.ModelViewSet):
    serializer_class = ExamSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(methods=['get'], detail=False)
    def get_exam_list(self, request):
        try:
            sessions = Exam.objects.filter(status__key='session_ready', is_finished=False).order_by('id')
            serializer = self.serializer_class(sessions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': f"{e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



    @action(methods=['get'], detail=False)
    def get_exam_name(self, request):
        exam_id = request.query_params.get('exam_id')
        if not exam_id:
            return Response({'message': 'exam_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            exam = Exam.objects.get(id=int(exam_id))
            serializer = ExamSerializer(exam)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': f"{e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)