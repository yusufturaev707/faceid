from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from region.models import Region
from region.serializers import RegionSerializer


class RegionViewSet(viewsets.ModelViewSet):
    serializer_class = RegionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Region.objects.all().order_by('number')

    @action(methods=['get'], detail=False)
    def get_region_name(self, request):
        region_number = request.query_params.get('region_number')
        if not region_number:
            return Response({'message': 'region_number parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            region = Region.objects.get(number=region_number)
            serializer = RegionSerializer(region)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': f"{e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
