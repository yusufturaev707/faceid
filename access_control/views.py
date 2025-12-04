from django.shortcuts import render
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
import base64
import datetime
from django.utils import timezone
from email import message_from_bytes
from email.policy import default

from supervisor.models import Supervisor, EventSupervisor
from access_control.models import NormalUserLog
from access_control.utils import resize_base64_image
from exam.models import ExamZoneSwingBar, StudentLog, Exam
from region.models import Region, Zone

logger = logging.getLogger(__name__)


def student_access_monitor(request):
    """Student access monitor page"""
    return render(request, 'access_control/monitor_page.html')


class HikvisionWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        """Hikvision webhook handler with WebSocket broadcast"""
        try:
            # Webhook ma'lumotlarini parse qilish
            parsed_data = self._parse_webhook_data(request)
            if not parsed_data:
                return self._error_response("Kamera oldida shaxs topilmadi!")

            # Turniketni tekshirish
            turnstile_result = self._validate_turnstile(parsed_data)
            if turnstile_result['error']:
                self._send_websocket_error(0, parsed_data, turnstile_result['message'])
                return self._error_response(turnstile_result['message'])

            exam_sb = turnstile_result['exam_sb']
            turnstile_id = exam_sb.sb.id

            shift_number = self._get_current_shift(exam_sb.exam, parsed_data['datetime'])
            if not shift_number:
                message = "Hozir kirish vaqti emas!"
                self._send_websocket_error(turnstile_id, parsed_data, message)
                return self._error_response(message)

            if parsed_data['user_type'] == 'visitor':
                # Talabani tekshirish va ruxsat berish
                return self._process_student_access(
                    exam_sb,
                    turnstile_id,
                    shift_number,
                    parsed_data
                )
            # Faqat staff yoki nazoratchi uchun tekshirish
            if parsed_data['user_type'] == "normal":
                print(f"Normal user keldi: {parsed_data.get('name')}")
                logger.info(f"Normal user keldi: {parsed_data.get('name')}")
                return self._process_normal_user_access(
                    exam_sb,
                    turnstile_id,
                    shift_number,
                    parsed_data
                )
            # ✅ Agar user_type na 'visitor', na 'normal' bo'lmasa
            return self._error_response("Noma'lum foydalanuvchi turi!")
        except Exception as e:
            logger.exception(f"Webhook xatolik: {str(e)}")
            return self._error_response(f"Tizim xatoligi: {str(e)}")

    @staticmethod
    def _parse_webhook_data(request):
        """Webhook ma'lumotlarini parse qilish"""
        try:
            raw_data = request.body
            content_type = request.content_type or ''

            msg = message_from_bytes(
                b'Content-Type: ' + content_type.encode() + b'\r\n\r\n' + raw_data,
                policy=default
            )
            data = {}
            for part in msg.iter_parts():
                content_disposition = part.get('Content-Disposition', '')

                if 'name="AccessControllerEvent"' in content_disposition:
                    json_data = part.get_content()
                    data_dict = json.loads(json_data)

                    # Faqat active AccessControllerEvent ni qayta ishlash
                    if (data_dict.get("eventState") != "active" or
                            data_dict.get("eventType") != "AccessControllerEvent"):
                        return None

                    event = data_dict.get('AccessControllerEvent', {})

                    # Datetime ni to'g'ri parse qilish
                    dt = datetime.datetime.fromisoformat(data_dict["dateTime"])
                    if dt.tzinfo:
                        dt = dt.astimezone(timezone.get_current_timezone()).replace(tzinfo=None)
                    else:
                        dt = dt.replace(tzinfo=None)
                    data = {
                        'ip_address': data_dict.get("ipAddress"),
                        'mac_address': data_dict.get("macAddress"),
                        'door_no': event.get("doorNo"),
                        'datetime': dt,
                        'name': event.get("name", ""),
                        'employee_no': event.get("employeeNoString", ""),
                        'user_type': event.get("userType", ""),
                    }
                elif 'name="Picture"' in content_disposition:
                    image_data = part.get_content()
                    base64_string = base64.b64encode(image_data).decode('utf-8')
                    base64_string = resize_base64_image(base64_string)
                    data['live_image'] = base64_string
            return data
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Parse xatolik: {str(e)}")
            return None

    @staticmethod
    def _validate_turnstile(parsed_data):
        """Turniketni tekshirish"""
        from exam.models import ExamZoneSwingBar

        mac_address = parsed_data['mac_address']
        exam_sb_objects = ExamZoneSwingBar.objects.filter(
            sb__mac_address=mac_address,
            status=True,
            exam__is_finished=False
        ).select_related('sb', 'sb__zone', 'exam')

        if not exam_sb_objects.exists():
            return {
                'error': True,
                'message': 'Bu turniket topilmadi!',
                'exam_sb': None
            }

        return {
            'error': False,
            'message': None,
            'exam_sb': exam_sb_objects.first()
        }

    @staticmethod
    def _get_current_shift(exam, current_datetime):
        """Joriy shift raqamini aniqlash"""
        from exam.models import ExamShift

        shift_objects = ExamShift.objects.filter(
            exam=exam
        ).select_related('sm').order_by('sm__number')

        current_date = current_datetime.date()
        current_time = current_datetime.time()

        for shift in shift_objects:
            # Vaqtni to'g'ri solishtirish
            if shift.access_time <= current_time <= shift.expire_time:
                return shift.sm.number

        return None

    def _process_student_access(self, exam_sb, turnstile_id, shift_number, parsed_data):
        """Talabaning kirishini qayta ishlash"""
        from exam.models import Student, StudentPsData, ExamShift

        current_date = parsed_data['datetime'].date()
        employee_no = parsed_data['employee_no']

        # Talabani topish
        try:
            student = Student.objects.select_related(
                'exam', 'zone'
            ).get(
                exam=exam_sb.exam,
                imei=employee_no,
                e_date=current_date,
                sm=shift_number
            )
        except Student.DoesNotExist:
            queryset = Student.objects.filter(exam=exam_sb.exam, imei=employee_no).order_by('id')

            ws_data = {
                'status': 'error',
                'access_granted': False,
                'turnstile_id': turnstile_id,
                'turnstile_info': self._get_turnstile_info(parsed_data),
                'event': self._get_event_info(parsed_data),
                'student': {},
                'message': '',
                'timestamp': timezone.now().isoformat()
            }
            message = 'Joriy smenada topilmadi!'
            if not queryset.exists():
                message = 'Bu testda topilmadi!'
                ws_data['message'] = message
            else:
                student = queryset.first()
                student_ps_data = StudentPsData.objects.get(student=student)
                ws_data['message'] = message
                ws_data['student'] = self._get_student_info(student, student_ps_data, f"{student.sm}-smena")

                try:
                    StudentLog.objects.create(
                        student=student,
                        door=parsed_data['door_no'],
                        ip_address=parsed_data['ip_address'],
                        mac_address=parsed_data['mac_address'],
                        employee_no=parsed_data['employee_no'],
                        direction='entry' if parsed_data['door_no'] == 1 else 'exit' if parsed_data[
                                                                                            'door_no'] == 2 else 'unknown',
                        requires_verification=True,
                        img_face=parsed_data['live_image'],
                        status='denied',
                        pass_time=parsed_data['datetime']
                    )
                except Exception as e:
                    print(e)

            self._send_websocket_message(turnstile_id, ws_data)
            return self._error_response(message)

        # Shift nomini olish
        shift_name = ExamShift.objects.get(
            exam=exam_sb.exam,
            sm__number=shift_number
        ).sm.name

        # Talaba ma'lumotlarini olish
        try:
            student_ps_data = StudentPsData.objects.get(student=student)
        except StudentPsData.DoesNotExist:
            student_ps_data = None

        # Tekshiruvlar
        is_same_zone = (student.zone_id == exam_sb.sb.zone_id)
        is_not_cheating = not student.is_cheating

        # Ruxsat berish shartlari
        if is_same_zone and is_not_cheating:
            is_opened = self._grant_access(
                exam_sb, turnstile_id, student,
                student_ps_data, shift_name, parsed_data
            )
            if is_opened:
                try:
                    StudentLog.objects.create(
                        student=student,
                        door=parsed_data['door_no'],
                        ip_address=parsed_data['ip_address'],
                        mac_address=parsed_data['mac_address'],
                        employee_no=parsed_data['employee_no'],
                        direction='entry' if parsed_data['door_no'] == 1 else 'exit' if parsed_data['door_no'] == 2 else 'unknown',
                        requires_verification=True,
                        img_face=parsed_data['live_image'],
                        status='approved',
                        pass_time=parsed_data['datetime']
                    )
                except Exception as e:
                    print(e)
                return self._success_response()
            else:
                try:
                    StudentLog.objects.create(
                        student=student,
                        door=parsed_data['door_no'],
                        ip_address=parsed_data['ip_address'],
                        mac_address=parsed_data['mac_address'],
                        employee_no=parsed_data['employee_no'],
                        direction='entry' if parsed_data['door_no'] == 1 else 'exit' if parsed_data['door_no'] == 2 else 'unknown',
                        requires_verification=True,
                        img_face=parsed_data['live_image'],
                        status='not_open',
                        pass_time=parsed_data['datetime']
                    )
                except Exception as e:
                    print(e)
                return self._error_response("Eshik ochilmadi")
        else:
            try:
                StudentLog.objects.create(
                    student=student,
                    door=parsed_data['door_no'],
                    ip_address=parsed_data['ip_address'],
                    mac_address=parsed_data['mac_address'],
                    employee_no=parsed_data['employee_no'],
                    direction='entry' if parsed_data['door_no'] == 1 else 'exit' if parsed_data[
                                                                                        'door_no'] == 2 else 'unknown',
                    requires_verification=True,
                    img_face=parsed_data['live_image'],
                    status='denied',
                    pass_time=parsed_data['datetime']
                )
            except Exception as e:
                print(e)

            return self._deny_access(
                turnstile_id, student, student_ps_data,
                shift_name, parsed_data, is_same_zone, is_not_cheating
            )

    def _process_normal_user_access(self, exam_sb, turnstile_id, shift_number, parsed_data):
        """Normal user kirishini qayta ishlash"""
        employee_no = parsed_data['employee_no']
        current_datetime = parsed_data['datetime']
        current_date = current_datetime.date()
        exam = exam_sb.exam

        e_supervisor_queryset = EventSupervisor.objects.filter(supervisor__imei=employee_no, exam=exam, supervisor__status=True)
        role = 'unknown'

        if not e_supervisor_queryset.exists():
            message = "Siz topilmadingiz!"
            ws_data = {
                'status': 'error',
                'access_granted': False,
                'turnstile_id': turnstile_id,
                'turnstile_info': self._get_turnstile_info(parsed_data),
                'event': self._get_event_info(parsed_data),
                'student': None,
                'role': role,
                'zone': None,
                'message': message,
                'timestamp': timezone.now().isoformat()
            }

            self._send_websocket_message(turnstile_id, ws_data)
            return self._error_response(message)

        normal_user = e_supervisor_queryset.first()

        if normal_user.supervisor.role == 'supervisor':
            q_supervisor = e_supervisor_queryset.filter(test_date=current_date, sm=shift_number)
            if q_supervisor.exists():
                supervisor_ob = q_supervisor.first()

                is_opened = self._grant_access_normal_user(
                    exam_sb, turnstile_id, supervisor_ob, parsed_data
                )

                supervisor_ob.is_participated = True
                supervisor_ob.save()

                if is_opened:
                    try:
                        NormalUserLog.objects.create(
                            normal_user_id=supervisor_ob.id,
                            normal_user_type=normal_user.supervisor.role,
                            zone = exam_sb.sb.zone,
                            employee_no=employee_no,
                            last_name=normal_user.supervisor.last_name,
                            first_name=normal_user.supervisor.first_name,
                            middle_name=normal_user.supervisor.middle_name,
                            img_face=parsed_data['live_image'],
                            door=parsed_data['door_no'],
                            pass_time=parsed_data['datetime'],
                            ip_address=parsed_data['ip_address'],
                            mac_address=parsed_data['mac_address'],
                            direction='entry' if parsed_data['door_no'] == 1 else 'exit' if parsed_data[
                                                                                                'door_no'] == 2 else 'unknown',
                            status='approved',
                        )
                    except Exception as e:
                        print(e)
                    return self._success_response()
                else:
                    try:
                        NormalUserLog.objects.create(
                            normal_user_id=normal_user.id,
                            normal_user_type=normal_user.supervisor.role,
                            zone = exam_sb.sb.zone,
                            employee_no=employee_no,
                            last_name=normal_user.supervisor.last_name,
                            first_name=normal_user.supervisor.first_name,
                            middle_name=normal_user.supervisor.middle_name,
                            img_face=parsed_data['live_image'],
                            door=parsed_data['door_no'],
                            pass_time=parsed_data['datetime'],
                            ip_address=parsed_data['ip_address'],
                            mac_address=parsed_data['mac_address'],
                            direction='entry' if parsed_data['door_no'] == 1 else 'exit' if parsed_data[
                                                                                                'door_no'] == 2 else 'unknown',
                            status='not_open',
                        )
                    except Exception as e:
                        print(e)
                    return self._error_response("Eshik ochilmadi")
            else:
                try:
                    NormalUserLog.objects.create(
                        normal_user_id=normal_user.id,
                        normal_user_type=normal_user.supervisor.role,
                        zone = exam_sb.sb.zone,
                        employee_no=employee_no,
                        last_name=normal_user.supervisor.last_name,
                        first_name=normal_user.supervisor.first_name,
                        middle_name=normal_user.supervisor.middle_name,
                        img_face=parsed_data['live_image'],
                        door=parsed_data['door_no'],
                        pass_time=parsed_data['datetime'],
                        ip_address=parsed_data['ip_address'],
                        mac_address=parsed_data['mac_address'],
                        direction='entry' if parsed_data['door_no'] == 1 else 'exit' if parsed_data[
                                                                                            'door_no'] == 2 else 'unknown',
                        status='not_open',
                    )
                except Exception as e:
                    print(e)

                ws_data = {
                    'status': 'error',
                    'access_granted': False,
                    'turnstile_id': turnstile_id,
                    'turnstile_info': self._get_turnstile_info(parsed_data),
                    'event': self._get_event_info(parsed_data),
                    'student': None,
                    'message': '',
                    'timestamp': timezone.now().isoformat()
                }
                self._send_websocket_message(turnstile_id, ws_data)
                return self._error_response("Eshik ochilmadi")
        elif normal_user.supervisor.role == 'staff':
            is_opened = self._grant_access_normal_user(
                exam_sb, turnstile_id, normal_user, parsed_data
            )

            normal_user.is_participated = True
            normal_user.save()

            if is_opened:
                try:
                    NormalUserLog.objects.create(
                        normal_user_id=normal_user.id,
                        normal_user_type=normal_user.supervisor.role,
                        zone = exam_sb.sb.zone,
                        employee_no = employee_no,
                        last_name = normal_user.supervisor.last_name,
                        first_name = normal_user.supervisor.first_name,
                        middle_name = normal_user.supervisor.middle_name,
                        img_face=parsed_data['live_image'],
                        door=parsed_data['door_no'],
                        pass_time=parsed_data['datetime'],
                        ip_address=parsed_data['ip_address'],
                        mac_address=parsed_data['mac_address'],
                        direction='entry' if parsed_data['door_no'] == 1 else 'exit' if parsed_data['door_no'] == 2 else 'unknown',
                        status='approved',
                    )
                except Exception as e:
                    print(e)
                return self._success_response()
            else:
                try:
                    NormalUserLog.objects.create(
                        normal_user_id=normal_user.id,
                        normal_user_type=normal_user.supervisor.role,
                        zone = exam_sb.sb.zone,
                        employee_no=employee_no,
                        last_name=normal_user.supervisor.last_name,
                        first_name=normal_user.supervisor.first_name,
                        middle_name=normal_user.supervisor.middle_name,
                        img_face=parsed_data['live_image'],
                        door=parsed_data['door_no'],
                        pass_time=parsed_data['datetime'],
                        ip_address=parsed_data['ip_address'],
                        mac_address=parsed_data['mac_address'],
                        direction='entry' if parsed_data['door_no'] == 1 else 'exit' if parsed_data[
                                                                                            'door_no'] == 2 else 'unknown',
                        status='not_open',
                    )
                except Exception as e:
                    print(e)
                return self._error_response("Eshik ochilmadi")
        else:
            pass


    def _grant_access(self, exam_sb, turnstile_id, student, student_ps_data, shift_name, parsed_data):
        """Ruxsat berish va eshikni ochish"""
        from access_control.services import BarrierControlService

        # Eshikni ochish
        sb_config = BarrierControlService(
            parsed_data['ip_address'],
            exam_sb.sb.username,
            exam_sb.sb.password,
            parsed_data['door_no']
        )

        is_opened = sb_config.send_approval(approve=True)

        # WebSocket xabari
        ws_data = {
            'status': 'success' if is_opened else 'error2',
            'access_granted': is_opened,
            'turnstile_id': turnstile_id,
            'turnstile_info': self._get_turnstile_info(parsed_data),
            'student': self._get_student_info(student, student_ps_data, shift_name),
            'event': self._get_event_info(parsed_data),
            'message': 'Ruxsat' if is_opened else 'Eshik ochilmadi',
            'timestamp': timezone.now().isoformat()
        }

        self._send_websocket_message(turnstile_id, ws_data)

        logger.info(
            f"Student {student.id} - {'Kirdi' if is_opened else 'Eshik ochilmadi'} "
            f"- Turniket #{turnstile_id}"
        )
        return is_opened

    def _grant_access_normal_user(self, exam_sb, turnstile_id, normal_user, parsed_data):
        """Normal user uchun ruxsat berish va eshikni ochish"""
        from access_control.services import BarrierControlService

        # Eshikni ochish
        sb_config = BarrierControlService(
            parsed_data['ip_address'],
            exam_sb.sb.username,
            exam_sb.sb.password,
            parsed_data['door_no']
        )

        is_opened = sb_config.send_approval(approve=True)

        # WebSocket xabari
        ws_data = {
            'status': 'success' if is_opened else 'error',
            'access_granted': is_opened,
            'turnstile_id': turnstile_id,
            'turnstile_info': self._get_turnstile_info(parsed_data),
            'student': None,
            'ps_image': normal_user.supervisor.img_b64 if normal_user.supervisor.img_b64 else '',
            'role': normal_user.supervisor.role,
            'zone': f"{normal_user.zone.region.name}",
            'event': self._get_event_info(parsed_data),
            'message': 'Ruxsat' if is_opened else 'Eshik ochilmadi',
            'timestamp': timezone.now().isoformat()
        }

        self._send_websocket_message(turnstile_id, ws_data)

        logger.info(
            f"NormalUser {normal_user.supervisor.imei} - {'Kirdi' if is_opened else 'Eshik ochilmadi'} "
            f"- Turniket #{turnstile_id}"
        )
        return is_opened

    def _deny_access(self, turnstile_id, student, student_ps_data, shift_name, parsed_data, is_same_zone, is_not_cheating):
        """Ruxsat rad etish"""
        if not is_not_cheating:
            message = "Chetlashtirilgan!"
        elif not is_same_zone:
            message = "Boshqa hudud"
        else:
            message = "Ruxsat yo'q."

        ws_data = {
            'status': 'error3',
            'access_granted': False,
            'turnstile_id': turnstile_id,
            'turnstile_info': self._get_turnstile_info(parsed_data),
            'student': self._get_student_info(student, student_ps_data, shift_name),
            'event': self._get_event_info(parsed_data),
            'role': 'visitor',
            'message': message,
            'timestamp': timezone.now().isoformat()
        }

        self._send_websocket_message(turnstile_id, ws_data)
        logger.warning(f"Student {student.id} - {message} - Turniket #{turnstile_id}")

        return self._error_response('Access denied')

    def _deny_access_normal_user(self, turnstile_id, normal_user, message, parsed_data):
        """Normal user uchun ruxsat rad etish"""
        ws_data = {
            'status': 'error3',
            'access_granted': False,
            'turnstile_id': turnstile_id,
            'turnstile_info': self._get_turnstile_info(parsed_data),
            'student': None,
            'event': self._get_event_info(parsed_data),
            'role': normal_user.supervisor.role,
            'zone': normal_user.zone.name,
            'message': message,
            'timestamp': timezone.now().isoformat()
        }

        self._send_websocket_message(turnstile_id, ws_data)
        logger.warning(f"NormalUser {normal_user.id} - {message} - Turniket #{turnstile_id}")

        return self._error_response('Access denied')

    @staticmethod
    def _get_turnstile_info(parsed_data):
        """Turniket ma'lumotlari"""
        return {
            'ip': parsed_data['ip_address'],
            'mac': parsed_data['mac_address'],
            'door_no': parsed_data['door_no'],
        }

    @staticmethod
    def _get_student_info(student, student_ps_data, shift_name):
        """Talaba ma'lumotlari"""
        return {
            'id': student.id,
            'name': student.fio if student else "",
            'employee_no': student.imei,
            'exam': student.exam.name if hasattr(student.exam, 'name') else str(student.exam.id),
            'zone': student.zone.name if hasattr(student.zone, 'name') else str(student.zone.id),
            'test_day': str(student.e_date),
            'sm': shift_name,
            'group_number': getattr(student, 'gr_n', 'N/A'),
            'is_warning': getattr(student, 'is_blacklist', False),
            'photo': student_ps_data.img_b64 if student_ps_data else "",
        }

    @staticmethod
    def _get_event_info(parsed_data):
        """Event ma'lumotlari"""
        return {
            'datetime': parsed_data['datetime'].isoformat(),
            'door_no': parsed_data['door_no'],
            'ip_address': parsed_data['ip_address'],
            'mac_address': parsed_data['mac_address'],
            'employee_no': parsed_data.get('employee_no', ''),
            'name': parsed_data.get('name', ''),
            'user_type': parsed_data.get('user_type', ''),
        }

    @staticmethod
    def _send_websocket_message(turnstile_id, data):
        """WebSocket orqali xabar yuborish"""
        if not turnstile_id:
            logger.warning("Turniket ID topilmadi, WebSocket'ga yuborilmadi")
            return

        try:
            channel_layer = get_channel_layer()
            group_name = f'turnstile_{turnstile_id}'

            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'student_access_event',
                    'data': data
                }
            )
            logger.debug(f"WebSocket xabari yuborildi: {group_name}")
        except Exception as e:
            logger.error(f"WebSocket yuborishda xatolik: {str(e)}")

    def _send_websocket_error(self, turnstile_id, parsed_data, message):
        """WebSocket orqali xato xabari yuborish"""
        self._send_websocket_message(turnstile_id, {
            'status': 'error1',
            'access_granted': False,
            'turnstile_id': turnstile_id,
            'turnstile_info': self._get_turnstile_info(parsed_data),
            'event': self._get_event_info(parsed_data),
            'message': message,
            'timestamp': timezone.now().isoformat()
        })

    @staticmethod
    def _success_response():
        """Muvaffaqiyatli javob"""
        return Response({
            'status': 'success',
            'message': 'Access granted'
        }, status=status.HTTP_200_OK)

    @staticmethod
    def _error_response(message):
        """Xato javobi"""
        print(message)
        return Response({
            'status': 'error',
            'message': message
        }, status=status.HTTP_200_OK)


class ActiveExamListView(APIView):
    """Regionlar ro'yxatini qaytarish"""

    def get(self, request):
        try:
            exams = []
            exam_objects = Exam.objects.filter(status__key='ready', is_finished=False).order_by('-id')

            for item in exam_objects:
                exams.append({
                    'id': item.id,
                    'name': item.test.name,
                })

            return Response({
                'status': 'success',
                'data': exams
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ZoneListView(APIView):
    def get(self, request):
        try:
            buildings = []
            zone_objects = Zone.objects.filter(region=request.user.region, status=True).order_by('number')

            for zone in zone_objects:
                buildings.append({
                    'id': zone.id,
                    'name': zone.name if hasattr(zone, 'name') else f'Bino #{zone.id}',
                })

            return Response({
                'status': 'success',
                'data': buildings,
                'region_name': request.user.region.name if hasattr(request.user.region, 'name') else '-',
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TurnstileListView(APIView):
    def get(self, request):
        try:
            zone_id = request.GET.get('zone_id')

            if not zone_id:
                return Response({
                    'status': 'error',
                    'message': 'zone_id parameter required'
                }, status=status.HTTP_400_BAD_REQUEST)

            turnstiles = []

            exam_zone_sbs = ExamZoneSwingBar.objects.filter(
                sb__zone_id=zone_id, status=True
            ).select_related('sb').order_by('sb__id')

            for ezs in exam_zone_sbs:
                sb = ezs.sb
                turnstiles.append({
                    'id': sb.id,
                    'name': sb.name if hasattr(sb, 'name') else f'Turniket #{sb.id}',
                    'ip_address': sb.ip_address,
                    'mac_address': sb.mac_address,
                    'location': sb.location if hasattr(sb, 'location') else '',
                    'zone_id': zone_id,
                })

            return Response({
                'status': 'success',
                'data': turnstiles
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)