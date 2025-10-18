# from users.models import UserLog, User
#
#
# class UserActivityMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response
#
#     def __call__(self, request):
#         response = self.get_response(request)
#
#         if request.user.is_authenticated and not request.path.startswith('/static/'):
#             user = User.objects.get(pk=request.user.id)
#             UserLog.objects.create(
#                 user=user,
#                 user_role=user.role.name,
#                 action=f"Ko'rilgan URL: {request.path}",
#                 ip_address=request.META.get('REMOTE_ADDR'),
#                 status=UserLog.STATUS_CHOICES.SUCCESS
#             )
#         return response