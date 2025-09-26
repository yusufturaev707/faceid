from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        """Oddiy foydalanuvchi yaratish"""
        if not username:
            raise ValueError("Username kiritilishi shart")
        user = self.model(username=username)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        """Superuser yaratish"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)