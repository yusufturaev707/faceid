from django import forms
from unfold.widgets import UnfoldAdminSelectWidget, UnfoldAdminTextInputWidget, UnfoldAdminImageFieldWidget

from exam.models import Cheating


class ExclusionStudentForm(forms.ModelForm):
    class Meta:
        model = Cheating
        fields = ('imei', 'reason', 'pic')

        widgets = {
            'imei': UnfoldAdminTextInputWidget(attrs={
                'class': 'block w-full rounded-lg border-gray-300 shadow-sm '
                         'focus:border-blue-500 focus:ring-blue-500 '
                         'px-3 py-2 text-gray-900 bg-white',
                'placeholder': 'JSHSHIR kiriting...',
            }),

            'reason': UnfoldAdminSelectWidget(attrs={
                'class': (
                    'block w-full rounded-md border border-gray-300 bg-white '
                    'px-3 py-2 text-gray-900 shadow-sm transition-all '
                    'focus:border-blue-600 focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 '
                    'hover:border-gray-400'
                ),
            }),

            'pic': UnfoldAdminImageFieldWidget(attrs={
                'class': 'block w-full text-gray-900 file:bg-blue-600 '
                         'file:hover:bg-blue-700 file:text-white file:px-4 '
                         'file:py-2 file:rounded-lg file:border-0 mt-2 '
                         'cursor-pointer',
            }),
        }
