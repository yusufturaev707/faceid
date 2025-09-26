# from core.utils import cosine_similarity
# from celery import shared_task
#
#
# @shared_task
# def add(x, y):
#     return x + y
#
# @shared_task
# def compare_two_face(ps_img: str=None, lv_img: str=None):
#     converter1 = Base64ImageConverter(ps_img)
#     embeddings1_list, is_success1 = converter1.convert()
#
#     if not is_success1:
#         return {"status": "error", "message": "Pasportdagi rasmdan yuz aniqlay olmadi!"}
#
#     converter2 = Base64ImageConverter(lv_img)
#     embeddings2_list, is_success2 = converter2.convert()
#
#     if not is_success2:
#         return {"status": "error", "message": "Live rasmda yuz aniqlanmadi!"}
#
#     known_embedding = embeddings1_list[0]
#     results = []
#     counter = 0
#     for face in embeddings2_list:
#         similarity = cosine_similarity(face, known_embedding)
#         similarity_score = round(similarity * 100)
#         if similarity_score >= 40:
#             results.append(
#                 {
#                     "index": counter,
#                     "verified": True,
#                     "score": similarity_score
#                 }
#             )
#         else:
#             results.append(
#                 {
#                     "index": counter,
#                     "verified": False,
#                     "score": similarity_score
#                 }
#             )
#         counter += 1
#
#     scores = [result['score'] for result in results]
#     max_score = max(scores)
#     max_score_index = scores.index(max_score)
#
#     person = results[max_score_index]
#     is_verified = person['verified']
#     score_similarity = person['score']
#
#     if is_verified:
#         return {"status": "success", "message": "Yuz aniqlandi!", "score_similarity": score_similarity}
#     else:
#         return {"status": "error", "message": "Yuz aniqlanmadi!", "score_similarity": score_similarity}