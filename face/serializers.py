from rest_framework import serializers
from face.models import (FaceIdentification, )


class FaceIdentificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaceIdentification
        fields = ['first_image', 'second_image']