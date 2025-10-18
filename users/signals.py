# signals.py
# from django.contrib.auth.signals import user_logged_in
# from django.dispatch import receiver
# from users.models import UserLog
#
# @receiver(user_logged_in)
# def log_user_login(sender, request, user, **kwargs):
#     UserLog.objects.create(
#         user=user,
#         ip_address=get_client_ip(request),
#         user_agent=request.META.get('HTTP_USER_AGENT', ''),
#     )
#
# def get_client_ip(request):
#     x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#     if x_forwarded_for:
#         ip = x_forwarded_for.split(',')[0]
#     else:
#         ip = request.META.get('REMOTE_ADDR')
#     return ip