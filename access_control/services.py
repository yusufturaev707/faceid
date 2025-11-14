# ============= access_control/services.py =============

import logging
import requests
from requests.auth import HTTPDigestAuth
import xml.etree.ElementTree as ET

logger = logging.getLogger('access_control')


class BarrierControlService:
    """Hikvision barrier bilan ishlash servisi"""

    def __init__(self, ip, username, password, door_n):
        self.ip = ip
        self.username = username
        self.password = password
        self.door_n = door_n

        self.auth = HTTPDigestAuth(
            username=username,
            password=password
        )
        self.base_url = f"http://{ip}"

    def send_approval(self, request_id: str = "123", approve: bool = True, reason: str = "") -> bool:
        try:
            if approve:
                url = f"{self.base_url}/ISAPI/AccessControl/RemoteControl/door/{self.door_n}"

                xml_data = """<?xml version="1.0" encoding="UTF-8"?>
                <RemoteControlDoor>
                    <cmd>open</cmd>
                </RemoteControlDoor>"""

                response = requests.put(
                    url,
                    data=xml_data,
                    auth=self.auth,
                    headers={'Content-Type': 'application/xml'},
                    timeout=5
                )

                res_status = "<statusCode>1</statusCode>"

                if response.status_code == 200 and (res_status in response.text):
                    logger.info(f"✅ Barrier opened for request: {request_id}")
                    return True
                else:
                    logger.error(f"❌ Barrier open failed. Status: {response.status_code}")
                    return False
            else:
                # Rad etish - eshikni ochmaslik kifoya
                logger.info(f"🚫 Access denied for request: {request_id}. Reason: {reason}")
                return True

        except requests.RequestException as e:
            logger.error(f"Barrier communication error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in send_approval: {e}")
            return False

    def get_door_status(self, door_no: int = 1) -> dict:
        """Eshik holatini olish"""
        try:
            url = f"{self.base_url}/ISAPI/AccessControl/Door/{door_no}/status"

            response = requests.get(
                url,
                auth=self.auth,
                timeout=5
            )

            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.text
                }
            else:
                return {
                    'success': False,
                    'error': f'Status code: {response.status_code}'
                }

        except Exception as e:
            logger.error(f"Get door status error: {e}")
            return {
                'success': False,
                'error': str(e)
            }