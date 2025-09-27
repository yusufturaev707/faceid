from django.apps import AppConfig


class FaceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'face'

    def ready(self):
        from django.conf import settings
        from insightface.app import FaceAnalysis

        if not hasattr(settings, 'FACE_ANALYSIS_MODEL') or settings.FACE_ANALYSIS_MODEL is None:
            try:
                settings.FACE_ANALYSIS_MODEL = FaceAnalysis(providers=['CPUExecutionProvider'])
                settings.FACE_ANALYSIS_MODEL.prepare(ctx_id=0, det_size=(800, 800), det_thresh=0.3)
            except Exception as e:
                print(f"Error loading FaceAnalysis model: {e}")
                settings.FACE_ANALYSIS_MODEL = None