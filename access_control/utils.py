import datetime


def check_access_with_datetime(test_day, access_time, expire_time, current_date) -> bool:
    try:
        access_time = datetime.datetime.combine(test_day, access_time)
        expire_time = datetime.datetime.combine(test_day, expire_time)
        return access_time <= current_date <= expire_time
    except Exception as e:
        print(f"{e}")
        return False


import base64
import io
from PIL import Image


def resize_base64_image(base64_string, new_size=(297, 382)):
    # 1. Base64 satrdagi qo'shimcha prefikslarni (masalan, 'data:image/png;base64,') olib tashlash
    header = ""
    encoded_data = ""
    if 'base64,' in base64_string:
        img_data = base64_string.split(',')
        header = img_data[0]
        encoded_data = img_data[1]
    else:
        encoded_data = base64_string
        header = "data:image/jpeg;base64,"  # Asl formatni taxmin qilamiz, agar ma'lum bo'lmasa

    try:
        # 2. Base64 baytga dekodlash
        image_bytes = base64.b64decode(encoded_data)

        # 3. Bayt ma'lumotlarini xotiradagi tasvirga aylantirish
        image_stream = io.BytesIO(image_bytes)
        img = Image.open(image_stream)

        # 4. Tasvir o'lchamini o'zgartirish (Resize)
        # Agar faqat bir o'lchamni berib, nisbatni saqlamoqchi bo'lsangiz, img.thumbnail(new_size) dan foydalaning
        resized_img = img.resize(new_size)

        # 5. Yangi tasvirni yana bayt oqimiga saqlash (formatni saqlashga harakat qiladi)
        output_stream = io.BytesIO()
        # Asl formatni aniqlay olmasangiz, 'PNG' yoki 'JPEG' dan foydalaning
        resized_img.save(output_stream, format=img.format if img.format else 'JPEG')

        # 6. Bayt oqimini Base64 ga kodlash
        new_base64_bytes = base64.b64encode(output_stream.getvalue())
        new_base64_string = new_base64_bytes.decode('utf-8')

        # To'liq Data URI formatini qaytarish (agar kerak bo'lsa)
        res = f"{header}{new_base64_string}"
        return f"{header}{new_base64_string}"

    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        return base64_string