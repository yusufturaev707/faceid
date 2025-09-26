import requests

def get_image_from_personal_info(imi: str = None, ps: str = None):
    try:
        data = requests.get(url='https://imei_api.uzbmb.uz/compress', params={'imie': imi, 'ps': ps}, verify=False)
        if data.status_code != 200:
            print(f"{imi} xatolik aniqlandi")
            return ""
        if data.status_code == 200:
            image_b64 = str(data.json()['data']['photo'])
            return image_b64
    except Exception as e:
        print(f"{imi} xatolik aniqlandi: {e}")
        return ""

def replace_image_to_none_image():
    base64_image = ""
    return base64_image