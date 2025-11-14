import requests
from requests.auth import HTTPDigestAuth
import time
import logging
import csv
from datetime import datetime
from typing import List, Dict, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(f'sequential_import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SequentialImporter:
    """
    Bitta-bitta ketma-ket import - 100% ishonchli
    Hardware error ga mutlaqo bardoshli
    """

    def __init__(self, base_url: str, username: str, password: str,
                 base_delay: float = 0.3, max_retry: int = 10):
        """
        Args:
            base_delay: Har bir so'rov orasidagi minimal kutish vaqti (soniya)
            max_retry: Maksimal retry urinishlari
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.base_delay = base_delay
        self.max_retry = max_retry
        self.url = f"{self.base_url}/ISAPI/AccessControl/UserInfo/Record?format=json"

        # Session yaratish
        self.session = requests.Session()
        self.session.auth = HTTPDigestAuth(username, password)
        self.session.headers.update({'Content-Type': 'application/json'})

        # Statistika
        self.stats = {
            'success': 0,
            'failed': 0,
            'hardware_errors': 0,
            'total_retries': 0,
            'consecutive_hw_errors': 0,
            'max_consecutive_hw_errors': 0,
            'total': 0,
            'start_time': None,
            'last_success_time': None
        }

        # Adaptive delay
        self.current_delay = base_delay
        self.min_delay = base_delay
        self.max_delay = 5.0

    def _adjust_delay_on_success(self):
        """Success bo'lsa delay ni kamaytirish"""
        self.stats['consecutive_hw_errors'] = 0

        # Har 20 ta success dan keyin 10% tezroq
        if self.stats['success'] % 20 == 0 and self.current_delay > self.min_delay:
            old_delay = self.current_delay
            self.current_delay = max(self.current_delay * 0.9, self.min_delay)
            if old_delay != self.current_delay:
                logger.info(f"⚡ Delay kamaytrildi: {old_delay:.3f}s → {self.current_delay:.3f}s")

    def _adjust_delay_on_hw_error(self):
        """Hardware error bo'lsa delay ni oshirish"""
        self.stats['consecutive_hw_errors'] += 1
        self.stats['max_consecutive_hw_errors'] = max(
            self.stats['max_consecutive_hw_errors'],
            self.stats['consecutive_hw_errors']
        )

        old_delay = self.current_delay
        self.current_delay = min(self.current_delay * 2, self.max_delay)

        logger.warning(
            f"⚠ HW Error #{self.stats['consecutive_hw_errors']} | "
            f"Delay oshirildi: {old_delay:.3f}s → {self.current_delay:.3f}s"
        )

    def add_single_user(self, user_data: Dict) -> Tuple[bool, str]:
        """
        Bitta userni qo'shish - to'liq retry logic bilan

        Returns:
            (success: bool, error_message: str)
        """
        employee_no = user_data.get('employeeNo')

        payload = {
            "UserInfo": {
                "employeeNo": str(employee_no),
                "name": user_data.get('name', f'User {employee_no}'),
                "userType": user_data.get('userType', 'normal'),
                "gender": "male",
                "Valid": {
                    "enable": True,
                    "beginTime": "2025-10-08T00:00:00",
                    "endTime": "2025-10-08T23:59:59",
                    "timeType": "local",
                    "timeSegment": [
                        {
                            "beginTime": "06:00:00",
                            "endTime": "10:00:00"
                        }
                    ]
                },
                "doorRight": "1,2",
                "roomNumber": 5,
                "floorNumber": 2,
                "buildingNumber": "B",
                "belongGroup": "1",
                "numOfFace": 1,
                "checkUser": True
            }
        }

        # Karta ma'lumotlari
        # if 'cardNo' in user_data:
        #     payload["UserInfo"]["Valid"] = {
        #         "enable": True,
        #         "beginTime": user_data.get('beginTime', '2024-01-01T00:00:00'),
        #         "endTime": user_data.get('endTime', '2037-12-31T23:59:59')
        #     }
        #     payload["UserInfo"]["numOfCard"] = 1
        #     payload["UserInfo"]["RightPlan"] = [{
        #         "doorNo": 1,
        #         "planTemplateNo": user_data.get('planTemplateNo', '1')
        #     }]

        # Retry loop
        for attempt in range(self.max_retry):
            try:
                # So'rov yuborish
                response = self.session.post(self.url, json=payload, timeout=15)

                if response.status_code == 200:
                    # SUCCESS
                    self._adjust_delay_on_success()
                    self.stats['last_success_time'] = datetime.now()
                    return True, "Success"

                # Xatolik tekshirish
                response_text = response.text
                is_hw_error = any(indicator in response_text for indicator in
                                  ["805306369", "Device Error", "deviceError", "Device hardware error"])

                if is_hw_error:
                    self.stats['hardware_errors'] += 1
                    self._adjust_delay_on_hw_error()

                    # Progressive waiting: 3, 6, 9, 12, 15 soniya...
                    wait_time = 3 * (attempt + 1)

                    logger.warning(
                        f"HW Error user {employee_no} (attempt {attempt + 1}/{self.max_retry}) | "
                        f"Waiting {wait_time}s..."
                    )

                    time.sleep(wait_time)
                    self.stats['total_retries'] += 1
                    continue

                # 401 Unauthorized - session yangilash
                if response.status_code == 401:
                    logger.warning(f"401 Unauthorized - session yangilanmoqda...")
                    self.session = requests.Session()
                    self.session.auth = HTTPDigestAuth(self.username, self.password)
                    self.session.headers.update({'Content-Type': 'application/json'})
                    time.sleep(1)
                    self.stats['total_retries'] += 1
                    continue

                # Boshqa xatoliklar
                if attempt == self.max_retry - 1:
                    return False, f"HTTP {response.status_code}: {response_text[:200]}"

                # Oddiy retry
                time.sleep(1 * (attempt + 1))
                self.stats['total_retries'] += 1

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout user {employee_no} (attempt {attempt + 1})")
                if attempt == self.max_retry - 1:
                    return False, "Timeout"
                time.sleep(2)
                self.stats['total_retries'] += 1

            except Exception as e:
                logger.error(f"Exception user {employee_no}: {str(e)}")
                if attempt == self.max_retry - 1:
                    return False, f"Exception: {str(e)}"
                time.sleep(2)
                self.stats['total_retries'] += 1

        return False, "Max retries exceeded"

    def import_users(self, users: List[Dict], checkpoint_interval: int = 100) -> Dict:
        """
        Userlarni ketma-ket import qilish

        Args:
            users: User ma'lumotlari
            checkpoint_interval: Har nechta userdan keyin checkpoint yaratish
        """
        self.stats['total'] = len(users)
        self.stats['start_time'] = datetime.now()

        logger.info("=" * 70)
        logger.info("SEQUENTIAL IMPORT BOSHLANDI (100% ISHONCHLI)")
        logger.info(f"Jami userlar: {len(users)}")
        logger.info(f"Base delay: {self.base_delay}s")
        logger.info(f"Max retry: {self.max_retry}")
        logger.info(f"Checkpoint har {checkpoint_interval} user")
        logger.info("=" * 70)

        failed_users = []
        last_checkpoint = 0

        for idx, user_data in enumerate(users, 1):
            employee_no = user_data.get('employeeNo')

            # So'rov yuborish
            success, error_msg = self.add_single_user(user_data)

            if success:
                self.stats['success'] += 1
            else:
                self.stats['failed'] += 1
                failed_users.append({**user_data, 'error': error_msg})
                logger.error(f"❌ Failed: User {employee_no} - {error_msg}")

            # Progress (har 10 ta userdan keyin)
            if idx % 10 == 0 or idx == len(users):
                processed = self.stats['success'] + self.stats['failed']
                progress = (processed / self.stats['total']) * 100
                elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
                speed = processed / elapsed if elapsed > 0 else 0

                eta_seconds = (self.stats['total'] - processed) / speed if speed > 0 else 0
                eta_minutes = eta_seconds / 60

                logger.info(
                    f"📊 [{idx}/{len(users)}] | "
                    f"✓ {self.stats['success']} | "
                    f"✗ {self.stats['failed']} | "
                    f"⚠ HW:{self.stats['hardware_errors']} | "
                    f"🔄 Retry:{self.stats['total_retries']} | "
                    f"⚡ {speed:.1f} user/s | "
                    f"⏱ ETA: {eta_minutes:.1f}min | "
                    f"Delay: {self.current_delay:.2f}s"
                )

            # Checkpoint
            if idx - last_checkpoint >= checkpoint_interval:
                self._save_checkpoint(idx, failed_users)
                last_checkpoint = idx

            # Har bir so'rovdan keyin kutish
            time.sleep(self.current_delay)

        # Final
        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()

        logger.info("\n" + "=" * 70)
        logger.info("✅ IMPORT YAKUNLANDI")
        logger.info(f"Jami: {self.stats['total']}")
        logger.info(
            f"Muvaffaqiyatli: {self.stats['success']} ({self.stats['success'] / self.stats['total'] * 100:.2f}%)")
        logger.info(f"Xatolik: {self.stats['failed']}")
        logger.info(f"Hardware errors: {self.stats['hardware_errors']}")
        logger.info(f"Max consecutive HW errors: {self.stats['max_consecutive_hw_errors']}")
        logger.info(f"Total retries: {self.stats['total_retries']}")
        logger.info(f"Umumiy vaqt: {duration:.0f}s ({duration / 60:.1f} daqiqa)")
        logger.info(f"O'rtacha tezlik: {self.stats['total'] / duration:.2f} user/soniya")
        logger.info("=" * 70)

        if failed_users:
            self._save_failed_users(failed_users)

        return self.stats

    def _save_checkpoint(self, current_index: int, failed_users: List[Dict]):
        """Checkpoint yaratish"""
        filename = f'checkpoint_{current_index}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'

        with open(filename, 'w') as f:
            f.write(f"Checkpoint: {current_index}\n")
            f.write(f"Success: {self.stats['success']}\n")
            f.write(f"Failed: {self.stats['failed']}\n")
            f.write(f"HW Errors: {self.stats['hardware_errors']}\n")

        logger.info(f"💾 Checkpoint saqlandi: {filename}")

    def _save_failed_users(self, failed_users: List[Dict]):
        """Xatolik bo'lgan userlarni saqlash"""
        filename = f'failed_users_seq_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        if failed_users:
            keys = failed_users[0].keys()
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(failed_users)

            logger.info(f"💾 Xatolikli userlar: {filename}")

    @staticmethod
    def load_users_from_csv(filename: str) -> List[Dict]:
        """CSV dan yuklash"""
        users = []
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                users.append(row)
        return users


def main():
    """Ishlatish"""

    # SOZLAMALAR
    importer = SequentialImporter(
        base_url="http://192.0.0.64",
        username="admin",
        password="Dtm@13579",
        base_delay=0.3,  # Har bir so'rov orasida 300ms
        max_retry=10  # Har bir user uchun 10 marta urinish
    )

    # Test userlar
    users = []
    for i in range(1, 100):
        users.append({
            'employeeNo': i,
            'name': f'Xodim {i}',
            'userType': 'normal'
        })

    # Import
    print("\n🚀 Sequential import boshlanmoqda...")
    print("⚠ Bu sekin, lekin 100% ishonchli!\n")

    stats = importer.import_users(users, checkpoint_interval=100)

    print(f"\n✅ Natija:")
    print(f"   Success rate: {stats['success'] / stats['total'] * 100:.2f}%")
    print(f"   Total time: {(stats['end_time'] - stats['start_time']).total_seconds() / 60:.1f} minutes")


if __name__ == "__main__":
    main()