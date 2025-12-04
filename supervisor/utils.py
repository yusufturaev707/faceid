import base64
import json
import time
from io import BytesIO
import requests
from PIL import Image

from requests.exceptions import ConnectTimeout, RequestException
from requests.auth import HTTPDigestAuth
from region.contex_manager import hikvision_session
from supervisor.models import Supervisor

HEADER = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def is_same_mac_addresses(base_url: str = "") -> bool:
    api_url = f"{base_url}"
    return True

def is_check_healthy(ip_address: str = None, mac_address: str = None, username: str = None,
                     password: str = None) -> bool:
    auth = HTTPDigestAuth(username, password)
    api_url = f"http://{ip_address}/SDK/activateStatus"
    try:
        res = requests.get(api_url, auth=auth, timeout=10)
        if res.status_code == 200:
            if "<Activated>true</Activated>" in res.text:
                return True
            else:
                return False
        else:
            return False
    except ConnectTimeout as e:
        return False
    except RequestException as e:
        return False
    except Exception as e:
        print(f"{ip_address} - {e}")
        return False

def get_all_supervisor(ip_address: str, username: str, password: str) -> list:
    """Barcha visitorlarni pagination bilan olish"""
    api_url = f"http://{ip_address}/ISAPI/AccessControl/UserInfo/Search?format=json"
    all_visitors = []

    try:
        position = 0
        max_results = 50  # Har bir so'rovda 50 ta

        while True:
            payload = {
                "UserInfoSearchCond": {
                    "searchID": "1",
                    "searchResultPosition": position,
                    "maxResults": max_results,
                }
            }

            with hikvision_session(ip_address, username, password) as session:
                res = session.post(url=api_url, json=payload, timeout=10)

                if res.status_code == 200:
                    data = res.json()
                    total_matches = data.get('UserInfoSearch', {}).get('totalMatches', 0)
                    users = data.get('UserInfoSearch', {}).get('UserInfo', [])

                    print(f"Position {position}: {len(users)} ta user olindi")

                    # Agar userlar bo'lmasa, to'xtatish
                    if not users:
                        break

                    # Faqat visitorlarni filtrlash
                    visitors = [{"employeeNo": u.get('employeeNo')}
                                for u in users if u.get('userType') == 'visitor']

                    all_visitors.extend(visitors)

                    # Agar barcha userlar olingan bo'lsa, to'xtatish
                    if len(users) < max_results:
                        break

                    # Keyingi sahifaga o'tish
                    position += max_results
                else:
                    print(f"Xatolik: {res.status_code}")
                    break
            time.sleep(0.05)
        print(f"Jami userlar: {total_matches} | Jami visitorlar: {len(all_visitors)}")
        return all_visitors

    except Exception as e:
        print(f"{ip_address} - {e}")
        return all_visitors


def delete_all_supervisor_clean(ip_address, username, password):
    delete_url = f"http://{ip_address}/ISAPI/AccessControl/UserInfo/Delete?format=json"
    visitors = get_all_supervisor(ip_address, username, password)

    success_count = 0
    failed_list = []
    total = len(visitors)

    print(f"\n{'=' * 80}")
    print(f"O'chirishni boshlash: {total} ta visitor")
    print(f"{'=' * 80}\n")

    for i, visitor in enumerate(visitors, 1):
        emp_no = visitor.get('employeeNo')

        print(f"[{i}/{total}]")

        payload = {
            "UserInfoDelCond": {
                "EmployeeNoList": [visitor]
            }
        }

        try:
            with hikvision_session(ip_address, username, password) as session:
                response = session.put(url=delete_url, json=payload, timeout=10)

                if response.status_code == 200:
                    print(f"  ✓ O'chirildi")
                    success_count += 1
                else:
                    print(f"  ✗ Xatolik: {response.status_code}")
                    failed_list.append({"employeeNo": emp_no})

        except Exception as e:
            print(f"  ✗ Exception: {str(e)[:50]}")
            failed_list.append({"employeeNo": emp_no})

        # Delay
        time.sleep(0.5)

        if i % 50 == 0 and i < total:
            print(f"\n  ⏸ Progress: {i}/{total}, 2s kutish...\n")
            time.sleep(2)

    print(f"\n{'=' * 80}")
    print(f"✓ O'chirildi: {success_count}/{total}")
    print(f"✗ O'chmaganlar: {len(failed_list)}/{total}")
    print(f"{'=' * 80}\n")

    return total, success_count

def add_supervisor_to_swing_barr(ip_address: str, username: str, password: str, obj: Supervisor = None):
    imei: str = obj.imei
    name: str = obj.fio
    gender: str = "male" if obj.gender == 'M' else "female"
    user_type: str = 'normal'
    door_right = "1,2"
    check_user = True
    num_of_face = 0

    valid = {
        "enable": True,
        "beginTime": "2025-01-01T00:00:00",
        "endTime": "2030-12-31T23:59:59",
        "timeType": "local",
    }

    is_success = False

    with hikvision_session(ip_address, username, password) as session:
        base_url = f"http://{ip_address}/ISAPI/AccessControl/UserInfo/Record?format=json"
        payload = {
            "UserInfo": {
                "employeeNo": f"{imei}",
                "name": f"{name}",
                "userType": user_type,
                "gender": gender,
                 "Valid": valid,
                "doorRight": door_right,
                "numOfFace": num_of_face,
                "checkUser": check_user
            }
        }
        try:
            res = session.post(url=base_url, json=payload, timeout=10)
            if res.status_code == 200:
                is_success = True
            else:
                print(f"Turniket: {ip_address} - {imei} yuklanmadi: {res.status_code}")
            return is_success
        except Exception as e:
            print(f"Turniket: {ip_address} - {imei} yuklanmadi: {res.status_code}. Error: {e}")
            return is_success

def compress_image_to_limit(image_data, max_size_kb=200, quality_start=95):
    """
    Rasmni 200 KB gacha compress qilish
    """
    try:
        # Image obyektini yaratish
        img = Image.open(BytesIO(image_data))

        # RGBA bo'lsa RGB ga o'tkazish (JPEG uchun)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Alpha channel ni olib tashlash
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background

        # Progressiv sifat pasaytirish
        quality = quality_start
        output = BytesIO()

        while quality > 10:
            output.seek(0)
            output.truncate()

            # JPEG sifatida saqlash
            img.save(output, format='JPEG', quality=quality, optimize=True)
            size_kb = output.tell() / 1024

            if size_kb <= max_size_kb:
                output.seek(0)
                return output.read()

            quality -= 5

        # Agar sifat yetmasa, o'lchamini kichraytirish
        width, height = img.size
        scale_factor = 0.9

        while quality <= 10:
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)

            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            output.seek(0)
            output.truncate()
            img_resized.save(output, format='JPEG', quality=85, optimize=True)

            size_kb = output.tell() / 1024

            if size_kb <= max_size_kb:
                output.seek(0)
                return output.read()

            scale_factor -= 0.05

            if scale_factor < 0.3:  # Juda kichik bo'lmasligi uchun
                break

        # Oxirgi variant - eng kichik
        output.seek(0)
        return output.read()

    except Exception as e:
        print(f"Compress qilishda xatolik: {e}")
        return image_data  # Original ni qaytarish


def upload_single_supervisor_face_image(user_data, ip_address, username, password):
    base_url = f"http://{ip_address}/ISAPI/Intelligent/FDLib/FDSetUp?format=json"
    is_added = False

    try:
        base64_string = user_data.get("img64")
        f_pid = user_data.get("fpid")

        if not base64_string or not f_pid:
            print(f"FPID {f_pid}: Base64 yoki FPID topilmadi")
            return is_added

        # Base64 ni decode qilish
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]

        image_data = base64.b64decode(base64_string)
        original_size_kb = len(image_data) / 1024

        print(f"FPID {f_pid}: Original rasm hajmi: {original_size_kb:.2f} KB")

        # Agar 200 KB dan katta bo'lsa, compress qilish
        if original_size_kb > 200:
            print(f"FPID {f_pid}: Rasm 200 KB dan katta, compress qilinmoqda...")
            image_data = compress_image_to_limit(image_data, max_size_kb=200)
            compressed_size_kb = len(image_data) / 1024
            print(f"FPID {f_pid}: Compressed hajmi: {compressed_size_kb:.2f} KB")

            if compressed_size_kb > 200:
                print(f"FPID {f_pid}: Ogohlantirish - Rasm hali ham 200 KB dan katta!")

        # JSON data tayyorlash
        json_data = {
            "faceLibType": "blackFD",
            "FDID": "1",
            "FPID": f_pid
        }

        # Multipart files
        files = {
            "FaceDataRecord": (None, json.dumps(json_data), "application/json"),
            "img": ("face.jpg", BytesIO(image_data), "image/jpeg"),
        }

    except base64.binascii.Error as e:
        print(f"FPID {f_pid}: Base64 decode xatolik: {e}")
        return is_added
    except Exception as e:
        print(f"FPID {f_pid}: Ma'lumot tayyorlashda xatolik: {e}")
        return is_added

    # API ga so'rov yuborish
    with hikvision_session(ip_address, username, password) as session:
        try:
            res = session.put(base_url, files=files, timeout=15)

            if res.status_code == 200:
                is_added = True
                print(f"✓ FPID {f_pid}: Rasm muvaffaqiyatli yuklandi")
            else:
                is_added = False
                print(f"✗ FPID {f_pid}: Yuklash xatolik - Status: {res.status_code}, Response: {res.text[:200]}")

        except requests.exceptions.Timeout as e:
            print(f"✗ FPID {f_pid}: Timeout xatolik - {ip_address}")
            is_added = False
        except requests.exceptions.ConnectionError as e:
            print(f"✗ FPID {f_pid}: Connection xatolik - {ip_address}: {e}")
            is_added = False
        except Exception as e:
            print(f"✗ FPID {f_pid}: Noma'lum xatolik - {ip_address}: {e}")
            is_added = False

    return is_added