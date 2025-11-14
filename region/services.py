import asyncio
import aiohttp
from aiohttp import BasicAuth, ClientTimeout
import time
import logging
from typing import List, Dict, Tuple
import csv
from datetime import datetime
import hashlib
import re

# Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'hikvision_async_import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DigestAuth:
    """Custom Digest Authentication for aiohttp"""

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.nc = 0
        self.cnonce = None
        self.auth_params = None

    def parse_auth_header(self, auth_header: str) -> Dict:
        """WWW-Authenticate headerini parse qilish"""
        params = {}
        parts = auth_header.replace('Digest ', '').split(',')

        for part in parts:
            key_val = part.strip().split('=', 1)
            if len(key_val) == 2:
                key = key_val[0].strip()
                val = key_val[1].strip().strip('"')
                params[key] = val

        return params

    def generate_response(self, method: str, uri: str) -> str:
        """Digest response generatsiya qilish"""
        if not self.auth_params:
            return ""

        self.nc += 1
        self.cnonce = hashlib.md5(str(time.time()).encode()).hexdigest()[:16]

        realm = self.auth_params.get('realm', '')
        nonce = self.auth_params.get('nonce', '')
        qop = self.auth_params.get('qop', 'auth')
        opaque = self.auth_params.get('opaque', '')
        algorithm = self.auth_params.get('algorithm', 'MD5')

        # HA1 = MD5(username:realm:password)
        ha1 = hashlib.md5(f"{self.username}:{realm}:{self.password}".encode()).hexdigest()

        # HA2 = MD5(method:uri)
        ha2 = hashlib.md5(f"{method}:{uri}".encode()).hexdigest()

        # Response = MD5(HA1:nonce:nc:cnonce:qop:HA2)
        nc_str = f"{self.nc:08x}"
        response_str = f"{ha1}:{nonce}:{nc_str}:{self.cnonce}:{qop}:{ha2}"
        response = hashlib.md5(response_str.encode()).hexdigest()

        # Authorization header yaratish
        auth_header = (
            f'Digest username="{self.username}", '
            f'realm="{realm}", '
            f'nonce="{nonce}", '
            f'uri="{uri}", '
            f'qop={qop}, '
            f'nc={nc_str}, '
            f'cnonce="{self.cnonce}", '
            f'response="{response}", '
            f'opaque="{opaque}", '
            f'algorithm={algorithm}'
        )

        return auth_header


class HikvisionAsyncImporter:
    def __init__(self, base_url: str, username: str, password: str,
                 max_concurrent: int = 50, retry_attempts: int = 3,
                 request_timeout: int = 10):
        """
        Async Hikvision bulk import - 300-500 user/s tezlikda

        Args:
            base_url: Qurilma URL
            username: Admin username
            password: Admin password
            max_concurrent: Parallel so'rovlar soni (50 tavsiya)
            retry_attempts: Qayta urinishlar
            request_timeout: So'rov timeout (soniya)
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.max_concurrent = max_concurrent
        self.retry_attempts = retry_attempts
        self.request_timeout = request_timeout
        self.url = f"{self.base_url}/ISAPI/AccessControl/UserInfo/Record?format=json"

        # Statistika
        self.stats = {
            'success': 0,
            'failed': 0,
            'total': 0,
            'start_time': None,
            'end_time': None
        }

        # Semaphore - bir vaqtda nechta so'rov
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # Auth cache
        self.auth_cache = {}

    async def _make_digest_request(self, session: aiohttp.ClientSession, method: str, url: str, json_data: Dict = None) -> Tuple[int, str]:
        """Digest auth bilan so'rov"""

        # Birinchi so'rov - 401 olish uchun
        try:
            async with session.request(method, url, json=json_data) as resp:
                if resp.status == 200:
                    return resp.status, await resp.text()

                if resp.status == 401:
                    # WWW-Authenticate headerini olish
                    auth_header = resp.headers.get('WWW-Authenticate', '')

                    if 'Digest' in auth_header:
                        # Digest auth
                        digest = DigestAuth(self.username, self.password)
                        digest.auth_params = digest.parse_auth_header(auth_header)

                        uri = url.replace(self.base_url, '')
                        auth_value = digest.generate_response(method, uri)

                        # Ikkinchi so'rov - auth bilan
                        headers = {'Authorization': auth_value}
                        async with session.request(method, url, json=json_data, headers=headers) as resp2:
                            print(await resp2.text())
                            return resp2.status, await resp2.text()

                return resp.status, await resp.text()

        except Exception as e:
            return 0, str(e)

    async def add_single_user(self, session: aiohttp.ClientSession,
                              user_data: Dict) -> Tuple[bool, str, Dict]:
        """Bitta user qo'shish (async)"""

        async with self.semaphore:  # Parallel cheklash
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

            # Retry logic
            for attempt in range(self.retry_attempts):
                try:
                    if attempt > 0:
                        await asyncio.sleep(1)
                    status, text = await self._make_digest_request(
                        session, 'POST', self.url, payload
                    )

                    if status == 200:
                        await asyncio.sleep(0.05)
                        return True, "Success", user_data
                    else:
                        error_msg = f"HTTP {status}: {text[:100]}"
                        if attempt == self.retry_attempts - 1:
                            return False, error_msg, user_data

                        await asyncio.sleep(0.3 * (attempt + 1))

                except Exception as e:
                    error_msg = f"Exception: {str(e)}"
                    if attempt == self.retry_attempts - 1:
                        return False, error_msg, user_data

                    await asyncio.sleep(0.3 * (attempt + 1))

            return False, "Max retries exceeded", user_data

    async def import_users_batch(self, users: List[Dict]) -> List[Tuple[bool, str, Dict]]:
        """Batch userlarni import qilish"""

        timeout = ClientTimeout(total=self.request_timeout)
        connector = aiohttp.TCPConnector(limit=self.max_concurrent, limit_per_host=self.max_concurrent)

        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            tasks = [self.add_single_user(session, user) for user in users]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Exception larni handle qilish
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    processed_results.append((False, str(result), {}))
                else:
                    processed_results.append(result)

            return processed_results

    def import_users(self, users: List[Dict], batch_size: int = 10) -> Dict:
        """
        Ko'p userlarni import qilish (main method)

        Args:
            users: User ma'lumotlari
            batch_size: Har bir batch hajmi (500-1000 optimal)
        """
        self.stats['total'] = len(users)
        self.stats['start_time'] = datetime.now()

        logger.info("=" * 60)
        logger.info("ASYNC IMPORT BOSHLANDI")
        logger.info(f"Jami userlar: {len(users)}")
        logger.info(f"Max concurrent: {self.max_concurrent}")
        logger.info(f"Batch size: {batch_size}")
        logger.info("=" * 60)

        failed_users = []

        # Batchlarga bo'lish
        total_batches = (len(users) + batch_size - 1) // batch_size

        for batch_idx in range(0, len(users), batch_size):
            batch = users[batch_idx:batch_idx + batch_size]
            current_batch = batch_idx // batch_size + 1

            logger.info(f"\nBatch {current_batch}/{total_batches} jarayonda... ({len(batch)} users)")

            # Async batch import
            results = asyncio.run(self.import_users_batch(batch))

            # Natijalarni processing
            for success, message, user_data in results:
                if success:
                    self.stats['success'] += 1
                else:
                    self.stats['failed'] += 1
                    failed_users.append({**user_data, 'error': message})
                    if self.stats['failed'] % 10 == 0:  # Har 10 ta xatolikni log qilish
                        logger.warning(f"Failed count: {self.stats['failed']}")

            # Progress
            processed = self.stats['success'] + self.stats['failed']
            progress = (processed / self.stats['total']) * 100
            elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
            speed = processed / elapsed if elapsed > 0 else 0

            logger.info(f"Progress: {processed}/{self.stats['total']} ({progress:.1f}%)")
            logger.info(
                f"Speed: {speed:.1f} users/sec | Success: {self.stats['success']} | Failed: {self.stats['failed']}")

            # Batchlar orasida kichik pauza
            if batch_idx + batch_size < len(users):
                time.sleep(0.2)

        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()

        # Final report
        logger.info("\n" + "=" * 60)
        logger.info("IMPORT YAKUNLANDI")
        logger.info(f"Jami: {self.stats['total']}")
        logger.info(f"Muvaffaqiyatli: {self.stats['success']}")
        logger.info(f"Xatolik: {self.stats['failed']}")
        logger.info(f"Success rate: {(self.stats['success'] / self.stats['total'] * 100):.2f}%")
        logger.info(f"Umumiy vaqt: {duration:.2f} soniya ({duration / 60:.2f} daqiqa)")
        logger.info(f"O'rtacha tezlik: {self.stats['total'] / duration:.1f} user/soniya")
        logger.info("=" * 60)

        # Xatolikli userlarni saqlash
        if failed_users:
            self._save_failed_users(failed_users)

        return self.stats

    def _save_failed_users(self, failed_users: List[Dict]):
        """Xatolik bo'lgan userlarni CSV ga saqlash"""
        filename = f'failed_users_async_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        if failed_users:
            keys = failed_users[0].keys()
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(failed_users)

            logger.info(f"Xatolik bo'lgan userlar saqlandi: {filename}")

    @staticmethod
    def load_users_from_csv(filename: str) -> List[Dict]:
        """CSV fayldan yuklash"""
        users = []
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                users.append(row)
        return users

    @staticmethod
    def generate_test_users(count: int) -> List[Dict]:
        """Test uchun userlar generatsiya qilish"""
        users = []
        for i in range(1, count + 1):
            users.append({
                'employeeNo': i,
                'name': f'Xodim {i}',
                'userType': 'normal',
                # Agar karta kerak bo'lsa:
                # 'cardNo': f'CARD{i:06d}',
                # 'planTemplateNo': '1'
            })
        return users


def main():
    """Asosiy funksiya"""

    # Sozlamalar
    importer = HikvisionAsyncImporter(
        base_url="http://192.0.0.64",
        username="admin",
        password="Dtm@13579",
        max_concurrent=30,  # 30-100 oralig'ida test qiling
        retry_attempts=3,
        request_timeout=10
    )

    # Variant 1: CSV dan yuklash
    # users = importer.load_users_from_csv('users.csv')

    # Variant 2: Test userlar yaratish
    users = importer.generate_test_users(1000)  # 10,000 ta user

    # Import boshlash
    print("\nImport boshlanmoqda...\n")
    stats = importer.import_users(users, batch_size=10)

    # Natija
    print("\n" + "=" * 60)
    print("YAKUNIY NATIJA:")
    print(f"✅ Muvaffaqiyatli: {stats['success']}")
    print(f"❌ Xatolik: {stats['failed']}")
    print(f"⚡ Tezlik: {stats['total'] / (stats['end_time'] - stats['start_time']).total_seconds():.1f} user/s")
    print("=" * 60)


if __name__ == "__main__":
    main()