from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
from unfold.widgets import UnfoldAdminTextInputWidget
from users.models import User


class UserCreationForm(forms.ModelForm):
    """Yangi user qo'shish formasi"""
    password1 = forms.CharField(
        label='Parol',
        widget=UnfoldAdminTextInputWidget(attrs={
            'type': 'password',
            'autocomplete': 'new-password'
        }),
        strip=False,
        help_text="Parol kamida 8 ta belgidan iborat bo'lishi kerak"
    )
    password2 = forms.CharField(
        label='Parolni tasdiqlash',
        widget=UnfoldAdminTextInputWidget(attrs={
            'type': 'password',
            'autocomplete': 'new-password'
        }),
        strip=False,
        help_text="Tasdiqlash uchun yuqoridagi parolni qayta kiriting"
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'middle_name', 'region')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Parollar mos kelmayapti")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])  # Parolni hash qilish
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """User tahrirlash formasi"""
    password = ReadOnlyPasswordHashField(
        label="Parol",
        help_text=(
            "Parollar hash formatda saqlanadi. "
            '<a href="../password/">Parolni o\'zgartirish uchun shu formani ishlatilng</a>.'
        ),
    )

    class Meta:
        model = User
        fields = '__all__'