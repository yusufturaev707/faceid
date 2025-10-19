from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        """Oddiy foydalanuvchi yaratish"""
        if not username:
            raise ValueError("Username kiritilishi shart")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.is_active=True
        user.is_staff=True
        user.save(using=self._db)
        print("User saqlandi......")
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser is_staff=True bo\'lishi kerak')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser is_superuser=True bo\'lishi kerak')
        return self.create_user(username, password, **extra_fields)