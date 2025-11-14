from rest_framework import serializers

class ApprovalSerializer(serializers.Serializer):
    """Tasdiqlash/rad etish uchun serializer"""

    approve = serializers.BooleanField(default=True)
    reason = serializers.CharField(required=False, allow_blank=True)
    approved_by = serializers.CharField(required=False, allow_blank=True)