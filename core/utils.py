import requests
from core import const
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.utils.translation import gettext_lazy as _


def get_image_from_personal_info(imi: str = None, ps: str = None):
    try:
        data = requests.get(url=const.API_PM_URL, params={'imie': imi, 'ps': ps}, verify=False)
        if data.status_code != 200:
            return ""
        if data.status_code == 200:
            image_b64 = str(data.json()['data']['photo'])
            return image_b64
    except Exception as e:
        return ""

def replace_image_to_none_image():
    base64_image = ""
    return base64_image


def get_personal_data(imi: str = None, ps: str = None):
    try:
        data = requests.get(url=const.API_PM_URL, params={'imie': imi, 'ps': ps}, verify=False)
        data = data.json()
        if data['status'] == 0:
            return {
                "status": 0,
                "message": "Ma'lumot topilmadi!",
            }
        if data['status'] == 1:
            data = {
                "sname": str(data['data']['sname']),
                "fname": str(data['data']['fname']),
                "mname": str(data['data']['mname']),
                "sex": int(data['data']['sex']),
                "photo": str(data['data']['photo']),
                "status": 1,
                "message": "Ma'lumot yangilandi!",
            }
            return data
    except Exception as e:
        return {
                "status": 0,
                "message": f"{e}",
            }


# unfold callback

def environment_callback(request):
    """Muhit nomi."""
    env = getattr(settings, 'CURRENT_ENV', 'PROD')

    env_config = {
        'DEV': (_("DEVELOPMENT"), "primary"),
        'STAGING': (_("TESTING"), "info"),
        'PROD': (_("PRODUCTION"), "success"),
    }

    return env_config.get(env, (_("PRODUCTION"), "success"))


def environment_title_prefix_callback(request):
    """Brauzer sarlavhasi prefiksi."""
    env = getattr(settings, 'CURRENT_ENV', 'PROD')
    if env != 'PROD':
        return f"[{env}] "
    return ""


def dashboard_callback(request, context):
    """Dashboard sozlamalari."""
    # ✅ Bu yerda import qiling (funktsiya ichida!)
    from django.contrib.auth import get_user_model

    User = get_user_model()

    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()

    context.update({
        "navigation": [
            {
                "title": _("📊 Statistika"),
                "icon": "analytics",
                "type": "card",
                "cards": [
                    {
                        "title": _("Jami Foydalanuvchilar"),
                        "value": total_users,
                        "icon": "people",
                    },
                    {
                        "title": _("Faol Foydalanuvchilar"),
                        "value": active_users,
                        "icon": "check_circle",
                    },
                ],
            },
            {
                "title": _("🗂️ Tez Kirish"),
                "icon": "grid_view",
                "type": "model",
                "models": [
                    "users.user",
                    "auditlog.logentry",
                ]
            },
        ]
    })
    return context


def badge_callback(request):
    """Dashboard badge."""
    # ✅ Funktsiya ichida import
    from users.models import User

    yesterday = timezone.now() - timedelta(days=1)
    new_users = User.objects.filter(last_login__gte=yesterday).count()
    return new_users if new_users > 0 else None


def audit_badge_callback(request):
    """Audit log badge."""
    # ✅ Funktsiya ichida import
    from auditlog.models import LogEntry

    yesterday = timezone.now() - timedelta(days=1)
    count = LogEntry.objects.filter(timestamp__gte=yesterday).count()
    return count if count > 0 else None


def permission_callback(request):
    """Ruxsat tekshiruvi."""
    if not request.user.is_authenticated:
        return False
    return request.user.is_superuser or request.user.has_perm('users.view_user')