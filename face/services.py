import asyncio
from asgiref.sync import sync_to_async
from concurrent.futures import ProcessPoolExecutor

from face.face_embedder import FaceEmbedder
from core.const import default_embedding, default_image64
from exam.models import Student
from core.utils import get_image_from_personal_info

API_URL_CEFR = "http://stat.uzbmb.uz/stat/cefr-face/index?e_date={}&page={}"
API_URL_NATIONAL = "http://stat.uzbmb.uz/stat/national-face/index?e_date={}&page={}"
API_URL_IIV = "https://api-iiv.uzbmb.uz/api/get-iiv-candidates/?test_day={}&page={}"
HEADERS = {'Authorization': 'Token 655e34da70cf385dffae9be6f24edf9443bfbf1e'}

BATCH_SIZE = 500



def process_student(student_data: dict):
    try:
        face_embedder: FaceEmbedder = FaceEmbedder()
        img_base64 = student_data.get("img_b64")
        imei = student_data.get("imei")
        ps_ser = student_data.get("ps_ser", "")
        ps_num = student_data.get("ps_number", "")

        is_image = True
        is_face = True
        face_embedding = face_embedder.numpy_to_pgvector(default_embedding)

        # 1️⃣ Rasm mavjud emas — pasport ma'lumotlari orqali olish
        if not img_base64:
            ps_num = ps_num[-7:].zfill(7)

            img_base64 = get_image_from_personal_info(imei, f"{ps_ser}{ps_num}")

            if not img_base64:
                is_image = False
                img_base64 = str(default_image64).replace("\n", "")
            else:
                if not face_embedder.validate_base64(img_base64):
                    is_image = False
                    print("Invalid Base64 string. Must start with a valid image data URI prefix.")
                img_rgb = face_embedder.decode_base64(img_base64)
                embedding = face_embedder.get_embedding(img_rgb)
                if embedding is None:
                    is_face = False
                else:
                    face_embedding = face_embedder.numpy_to_pgvector(embedding)

        # 2️⃣ Rasm mavjud — embedding olish
        else:
            try:
                if not face_embedder.validate_base64(img_base64):
                    is_image = False
                    print("Invalid Base64 string. Must start with a valid image data URI prefix.")

                img_rgb = face_embedder.decode_base64(img_base64)
                embedding = face_embedder.get_embedding(img_rgb)
                if embedding is None:
                    is_face = False
                else:
                    face_embedding = face_embedder.numpy_to_pgvector(embedding)
            except Exception as e:
                print(f"[process_student] Base64 konvertatsiyada xato: {imei}: {e}")
                is_image = False

        return {
            "id": student_data["id"],
            "embedding": face_embedding,
            "img_b64": img_base64,
            "is_image": is_image,
            "is_face": is_face
        }

    except Exception as e:
        print(f"[process_student] Umumiy xatolik: {student_data.get('imei')}: {e}")
        return None


@sync_to_async
def save_users_to_db(users):
    try:
        if not users:
            return
        users = [u for u in users if u is not None and u.pk is not None]

        if not users:
            return
        Student.objects.bulk_update(
            users, ['embedding', 'img_b64', 'is_face', 'is_image'], batch_size=BATCH_SIZE
        )
    except Exception as e:
        print(f"save_users_to_db error: {e}")


async def main_worker(student_queryset):
    print(f"Processing {len(student_queryset)} students")
    loop = asyncio.get_running_loop()
    print(1)
    max_workers = 4
    print(2)

    student_data_list = [
        {
            "id": s.id,
            "imei": s.imei,
            "img_b64": s.img_b64,
            "ps_ser": s.ps_ser,
            "ps_number": s.ps_number
        }
        for s in student_queryset
    ]
    print(3)
    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        print("Pooling...")
        tasks = [
            loop.run_in_executor(pool, process_student, student)
            for student in student_data_list
        ]
        results = await asyncio.gather(*tasks)

        # None bo‘lmaganlarni olish
        results = [r for r in results if r]

        # ORM obyektlarini yangilash
        users = []
        for r in results:
            student = Student.objects.get(pk=r["id"])
            student.embedding = r["embedding"]
            student.img_b64 = r["img_b64"]
            student.is_image = r["is_image"]
            student.is_face = r["is_face"]
            users.append(student)
        await save_users_to_db(users)