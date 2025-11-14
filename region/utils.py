import base64
import json
import time
from io import BytesIO
import requests

from requests.auth import HTTPDigestAuth

from exam.models import Student, ExamZoneSwingBar, ExamShift
from region.contex_manager import hikvision_session

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
    except requests.exceptions.ConnectionError as e:
        return False
    except Exception as e:
        print(f"{ip_address} - {e}")
        return False


def get_all_visitors(ip_address: str, username: str, password: str) -> list:
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


def delete_all_visitors_clean(ip_address, username, password):
    """Visitorlarni o'chirish"""
    delete_url = f"http://{ip_address}/ISAPI/AccessControl/UserInfo/Delete?format=json"

    visitors = get_all_visitors(ip_address, username, password)

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

        if i % 10 == 0 and i < total:
            print(f"\n  ⏸ Progress: {i}/{total}, 2s kutish...\n")
            time.sleep(2)

    print(f"\n{'=' * 80}")
    print(f"✓ O'chirildi: {success_count}/{total}")
    print(f"✗ O'chmaganlar: {len(failed_list)}/{total}")
    print(f"{'=' * 80}\n")

    return total == success_count


def upload_user_face_image_b(user_images, ip_address, username, password):
    base_url = f"http://{ip_address}/ISAPI/Intelligent/FDLib/FDSetUp?format=json"
    success_count = 0
    error_count = 0
    error_images_imei = []
    for user in user_images:
        base64_string = user.get("img64")
        f_pid = user.get("fpid")
        try:
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            image_data = base64.b64decode(base64_string)
        except Exception as e:
            print(f"{ip_address} - {e}")
            break

        json_data = {
            "faceLibType": "blackFD",
            "FDID": "1",
            "FPID": f_pid
        }

        files = {
            "FaceDataRecord": (None, json.dumps(json_data), "application/json"),
            "img": ("face.jpg", BytesIO(image_data), "image/jpeg"),
        }
        with hikvision_session(ip_address, username, password) as session:
            try:
                res = session.put(base_url, files=files, timeout=10)
                if res.status_code == 200:
                    success_count += 1
                else:
                    error_images_imei.append(f_pid)
                    error_count += 1
            except requests.exceptions.ConnectionError as e:
                print(f"Turniket: {ip_address} - {base64_string}. Error: {e}")
            except Exception as e:
                print(f"Turniket: {ip_address} - {base64_string}. Error: {e}")
    return success_count, error_count, error_images_imei


def add_user_to_swing_barr(ip_address: str, username: str, password: str, obj: Student = None, sm_obj: ExamShift = None):
    imei: str = obj.imei
    name: str = obj.fio
    user_type: str = 'visitor'
    door_right = "1,2"
    check_user = True
    belong_group = "1"
    num_of_face = 0
    test_day = obj.e_date

    is_success = False

    valid = {
        "enable": True,
        "beginTime": f"{test_day}T{sm_obj.access_time}",
        "endTime": f"{test_day}T{sm_obj.expire_time}",
        "timeType": "local",
    }

    with hikvision_session(ip_address, username, password) as session:
        base_url = f"http://{ip_address}/ISAPI/AccessControl/UserInfo/Record?format=json"
        payload = {
            "UserInfo": {
                "employeeNo": f"{imei}",
                "name": f"{name}",
                "userType": user_type,
                "gender": "male",
                "Valid": valid,
                "doorRight": door_right,
                "roomNumber": 5,
                "floorNumber": 2,
                "buildingNumber": "B",
                "belongGroup": belong_group,
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


def push_data_main_worker(sb_queryset):
    success_count_user = 0
    error_count_user = 0
    success_count_img = 0
    error_count_img = 0

    error_users_imei: list = []

    for sb in sb_queryset:
        zone = sb.sb.zone
        exam = sb.exam
        ip_address = sb.sb.ip_address
        username = sb.sb.username
        password = sb.sb.password
        parts_day_queryset = ExamShift.objects.filter(exam=exam).order_by('id')
        student_queryset = Student.objects.filter(zone=zone).order_by('id')

        n_count = student_queryset.count()

        user_image_list = []

        for student in student_queryset:
            sm: int = int(student.sm)
            sm_obj = parts_day_queryset.filter(sm=sm).first()
            imei = student.imei

            is_success = add_user_to_swing_barr(sb.sb.ip_address, sb.sb.username, sb.sb.password, student, sm_obj)
            if is_success:
                success_count_user += 1
                user_image_list.append(
                    {
                        "fpid": imei,
                        "img64": student.ps_data.img_b64
                    }
                )
            else:
                error_count_user += 1
                error_users_imei.append(imei)
        time.sleep(5)

        success_count_img, error_count_img, error_images_imei = upload_user_face_image_b(user_image_list, ip_address, username, password)
        time.sleep(0.05)

        sb.unpushed_users_imei = error_users_imei
        sb.unpushed_images_imei = error_images_imei
        sb.real_count = n_count
        sb.pushed_user_count = success_count_user
        sb.pushed_image_count = success_count_img
        sb.err_user_count = error_count_user
        sb.err_image_count = error_count_img
        sb.save()

        time.sleep(0.05)

    return success_count_user, success_count_img, error_count_user, error_count_img