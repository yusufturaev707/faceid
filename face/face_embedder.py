import base64
import re

import cv2
import numpy as np
from typing import Optional
from django.conf import settings


class FaceEmbedder:
    def __init__(self):
        self.detector = settings.FACE_ANALYSIS_MODEL
        self._recognizer = None
        self.image_format = None

    def validate_base64(self, image: str) -> bool:
        base64_pattern = r"^data:image\/(jpeg|jpg|png|gif|bmp);base64,"
        match = re.match(base64_pattern, image)
        if not match:
            return False
        self.image_format = match.group(1)
        return True

    @staticmethod
    def decode_base64(image: str):
        image_base64_data = image.split(",")[1]
        img_data = base64.b64decode(image_base64_data)  # Base64 stringni dekodlash
        np_arr = np.frombuffer(img_data, np.uint8)  # Byte massivga aylantirish
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)  # Rasmni OpenCV formatida o'qish
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return img_rgb

    @staticmethod
    def numpy_to_pgvector(embedding: np.ndarray) -> list:
        if isinstance(embedding, list):
            embedding = np.array(embedding, dtype=np.float32)
        return embedding.tolist()

    @staticmethod
    def pgvector_to_numpy(vector_list: list) -> np.ndarray:
        return np.array(vector_list, dtype=np.float32)

    def get_embedding(self, image: str) -> Optional[np.ndarray]:
        detected_faces = self.detector.get(image)
        if detected_faces:
            face = detected_faces[0]
            embedding = face.embedding
            return embedding
        return None

    @staticmethod
    def compare_faces(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        t = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
        return round(t * 100)