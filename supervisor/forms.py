from django import forms


class ExcelImportForm(forms.Form):
    excel_file = forms.FileField(
        label='📤 Import uchun Excel fayl tanlang',
        help_text='Faqat **.xlsx** yoki **.xls** formatidagi fayllarni yuklang.',
        widget=forms.FileInput(attrs={
            'class':
                # ---- MUI Input ----
                'block w-full text-sm text-gray-700 '
                'border border-gray-300 rounded-lg px-4 py-3 '
                'focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:border-indigo-600 '
                'transition duration-200 ease-in-out '

                # ---- MUI File Button ----
                'file:mr-4 file:py-2 file:px-4 '
                'file:rounded-md file:border-0 '
                'file:bg-indigo-600 file:text-white '
                'file:hover:bg-indigo-700 file:cursor-pointer '
                'file:text-sm file:font-medium '
                ,

            'accept': '.xlsx,.xls',
        })
    )