from django.core.exceptions import ValidationError
from django.db.models.fields import DateField

from core.const import API_URL_CEFR, API_URL_NATIONAL, API_URL_IIV, HEADERS
from exam.models import Exam, Student, StudentPsData, StudentBlacklist
from region.models import Region, Zone
import asyncio
from datetime import datetime, timedelta
import aiohttp
from django.db import transaction
from asgiref.sync import sync_to_async
from concurrent.futures import ProcessPoolExecutor

BATCH_SIZE = 1000


def get_region(dtm_id: int = 0) -> Region:
    region_mapping = {r.number: r for r in Region.objects.all()}
    return region_mapping.get(dtm_id, region_mapping.get(14))

def get_zone(dtm_id: int = 0) -> Zone:
    zones = Zone.objects.filter(region__number=dtm_id).order_by("id")
    zone_mapping = {z.number: z for z in zones}
    return zone_mapping.get(1, zones.first())

def is_have_image(data: str=None)->bool:
    if data is None or len(data) == 0:
        return False
    return True

def is_exists_blacklist(imei: str) -> bool:
    return StudentBlacklist.objects.filter(imei=imei).exists()


async def fetch_total_pages_cefr_nct(session, url):
    """Jami sahifalar sonini olish."""
    try:
        async with session.get(url, ssl=False) as response:
            result = await response.json()
            if result['status'] == 1:
                return result['data']['_meta'].get("pageCount", 0)
            else:
                return 0
    except Exception as e:
        print(f"Error1: {e}")


async def fetch_total_pages_iiv(session, url):
    """Jami sahifalar sonini olish."""
    try:
        async with session.get(url, headers=HEADERS, ssl=False) as response:
            result = await response.json()
            return result['total_pages']
    except Exception as e:
        print(f"Error1: {e}")



async def fetch_data_cefr_nct(session, url, test_day, page):
    """Berilgan sahifadagi ma'lumotlarni olish."""
    try:
        async with session.get(url.format(test_day, page, ssl=False)) as response:
            result = await response.json()
            return result['data'].get("items", [])
    except Exception as e:
        print(f"Error3: {e}")


async def fetch_data_iiv(session, url, test_day, page):
    """Berilgan sahifadagi ma'lumotlarni olish."""
    try:
        async with session.get(url.format(test_day, page), headers=HEADERS, ssl=False) as response:
            result = await response.json()
            return result['results']
    except Exception as e:
        print(f"Error3: {e}")



@sync_to_async
def save_cefr_to_db(test_day: DateField, data, obj: Exam):
    try:
        students_to_create = [
            Student(
                s_code=user["id"],
                exam=obj,
                zone=get_zone(int(user['dtm_id'])),
                e_date=test_day,
                last_name=user["lname"],
                first_name=user["fname"],
                middle_name=user["mname"],
                sm=user['smen'],
                imei=str(user["imie"]),
                gr_n=user["group"],
                sp=0,
                is_image=is_have_image(user['data']),
                is_blacklist=is_exists_blacklist(str(user["imie"])),
            )
            for user in data
        ]
        with transaction.atomic():
            Student.objects.bulk_create(students_to_create, batch_size=BATCH_SIZE, ignore_conflicts=True)

            imei_list = [user["id"] for user in data]
            students_map = Student.objects.filter(
                s_code__in=imei_list,
                e_date=test_day,
                exam=obj
            ).in_bulk(field_name='s_code')

            ps_data_to_create = []
            for user in data:
                s_code = user["id"]
                student_obj = students_map.get(s_code)

                if student_obj:
                    ps_data_to_create.append(
                        StudentPsData(
                            student=student_obj,
                            ps_ser=user['psser'],
                            ps_num=int(user['psnum']),
                            phone=user["phone"],
                            img_b64=user["data"],
                        )
                    )
            StudentPsData.objects.bulk_create(ps_data_to_create, batch_size=BATCH_SIZE)
        return f"Student: {len(students_to_create)}, PsData: {len(ps_data_to_create)} yozildi."
    except Exception as e:
        print(f"Error2: {e}")
        raise ValidationError(f"Bazaga yozishda xatolik: {e}")


@sync_to_async
def save_nct_to_db(test_day: DateField, data, obj: Exam):
    try:
        students_to_create = [
            Student(
                s_code=user["id"],
                exam=obj,
                zone=get_zone(int(user['test_region_id'])),
                e_date=test_day,
                last_name=user["lname"],
                first_name=user["fname"],
                middle_name=user["mname"],
                sm=user['number_sm'],
                imei=str(user["imie"]),
                gr_n=user["group_number"],
                sp=user["seat"],
                is_image=is_have_image(user['image_base64']),
                is_blacklist=is_exists_blacklist(str(user["imie"])),
            )
            for user in data
        ]

        with transaction.atomic():
            Student.objects.bulk_create(students_to_create, batch_size=BATCH_SIZE, ignore_conflicts=True)

            imei_list = [user["id"] for user in data]
            students_map = Student.objects.filter(
                s_code__in=imei_list,
                e_date=test_day,
                exam=obj
            ).in_bulk(field_name='s_code')

            ps_data_to_create = []
            for user in data:
                s_code = user["id"]
                student_obj = students_map.get(s_code)

                if student_obj:
                    ps_data_to_create.append(
                        StudentPsData(
                            student=student_obj,
                            ps_ser=user['psser'],
                            ps_num=int(user['psnum']),
                            img_b64=user["image_base64"],
                        )
                    )
            StudentPsData.objects.bulk_create(ps_data_to_create, batch_size=BATCH_SIZE)
        return f"Student: {len(students_to_create)}, PsData: {len(ps_data_to_create)} yozildi."
    except Exception as e:
        print(f"Error2: {e}")
        raise ValidationError(f"Bazaga yozishda xatolik: {e}")


@sync_to_async
def save_iiv_to_db(test_day: DateField, data, obj: Exam):
    try:
        students_to_create = [
            Student(
                s_code=user["id"],
                exam=obj,
                zone=get_zone(int(user['dtm_id'])),
                e_date=test_day,
                last_name=user["last_name"],
                first_name=user["first_name"],
                middle_name=user["parent_name"],
                sm=user['sm_number'],
                imei=str(user["pinfl"]),
                gr_n=user["group_number"],
                sp=user["seat_number"],
                is_image=is_have_image(user['person_image']),
                is_blacklist=is_exists_blacklist(str(user["pinfl"])),
            )
            for user in data
        ]
        with transaction.atomic():
            Student.objects.bulk_create(students_to_create, batch_size=BATCH_SIZE, ignore_conflicts=True)

            imei_list = [user["id"] for user in data]
            students_map = Student.objects.filter(
                s_code__in=imei_list,
                e_date=test_day,
                exam=obj
            ).in_bulk(field_name='s_code')

            ps_data_to_create = []
            for user in data:
                s_code = user["id"]
                student_obj = students_map.get(s_code)

                if student_obj:
                    ps_data_to_create.append(
                        StudentPsData(
                            student=student_obj,
                            ps_ser=user['passport_series'],
                            ps_num=int(user['passport_number']),
                            img_b64=user["person_image"],
                        )
                    )
            StudentPsData.objects.bulk_create(ps_data_to_create, batch_size=BATCH_SIZE)
        return f"Student: {len(students_to_create)}, PsData: {len(ps_data_to_create)} yozildi."
    except Exception as e:
        print(f"Error2: {e}")
        raise ValidationError(f"Bazaga yozishda xatolik: {e}")



async def get_all_users_cefr(queryset_object: Exam = None):
    total_count = 0
    try:
        time_difference = queryset_object.finish_date - queryset_object.start_date
        one_day = timedelta(days=1)
        current_date = queryset_object.start_date
        test_days = [current_date]

        for i in range(time_difference.days):
            current_date += one_day
            test_days.append(current_date)

        async with aiohttp.ClientSession() as session:
            for test_day in test_days:
                total_pages: int = await fetch_total_pages_cefr_nct(session, API_URL_CEFR.format(test_day, 1))

                all_data = []
                for page in range(1, 10 + 1):
                    data = await fetch_data_cefr_nct(session, API_URL_CEFR, test_day, page)
                    all_data.extend(data)

                await save_cefr_to_db(test_day, all_data, queryset_object)
                total_count += len(all_data)
                print(f"Inserted {len(all_data)} items for test_day {test_day} into the database.")
                await asyncio.sleep(2)
            return total_count
    except Exception as e:
        print(e)
        return total_count


async def get_all_users_nct(queryset_object: Exam = None):
    total_count = 0
    try:
        time_difference = queryset_object.finish_date - queryset_object.start_date
        one_day = timedelta(days=1)
        current_date = queryset_object.start_date
        test_days = [current_date]

        for i in range(time_difference.days):
            current_date += one_day
            test_days.append(current_date)

        async with aiohttp.ClientSession() as session:
            for test_day in test_days:
                total_pages: int = await fetch_total_pages_cefr_nct(session, API_URL_NATIONAL.format(test_day, 1))

                all_data = []
                for page in range(1, 20 + 1):
                    data = await fetch_data_cefr_nct(session, API_URL_NATIONAL, test_day, page)
                    all_data.extend(data)

                await save_nct_to_db(test_day, all_data, queryset_object)
                total_count += len(all_data)
                print(f"Inserted {len(all_data)} items for test_day {test_day} into the database.")
                await asyncio.sleep(2)
            return total_count
    except Exception as e:
        print(e)
        return total_count


async def get_all_users_iiv(queryset_object: Exam = None):
    total_count = 0
    try:
        time_difference = queryset_object.finish_date - queryset_object.start_date
        one_day = timedelta(days=1)
        current_date = queryset_object.start_date
        test_days = [current_date]

        for i in range(time_difference.days):
            current_date += one_day
            test_days.append(current_date)

        async with aiohttp.ClientSession() as session:
            for test_day in test_days:
                total_pages: int = await fetch_total_pages_iiv(session, API_URL_IIV.format(test_day, 1))

                all_data = []
                for page in range(1, 20 + 1):
                    data = await fetch_data_iiv(session, API_URL_IIV, test_day, page)
                    all_data.extend(data)

                await save_iiv_to_db(test_day, all_data, queryset_object)
                total_count += len(all_data)
                print(f"Inserted {len(all_data)} items for test_day {test_day} into the database.")
                await asyncio.sleep(2)
            return total_count
    except Exception as e:
        print(e)
        return total_count