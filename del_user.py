from contextlib import contextmanager
import requests
from requests.auth import HTTPDigestAuth


def get_all_visitors(ip_address: str, session: requests.Session) -> list:
    """Session bilan ishlash"""
    api_url = f"http://{ip_address}/ISAPI/AccessControl/UserInfo/Search?format=json"
    all_visitors = []
    try:
        payload = {
            "UserInfoSearchCond": {
                "searchID": "1",
                "searchResultPosition": 0,
                "maxResults": 10000,
                "userType": "normal"
            }
        }
        res = session.post(url=api_url, json=payload, timeout=10)
        if res.status_code == 200:
            data = res.json()
            total_user = data.get('UserInfoSearch', {}).get('totalMatches', 0)
            all_users = data.get('UserInfoSearch', {}).get('UserInfo', [])
            visitor_users = [{"employeeNo": u.get('employeeNo')}
                           for u in all_users if u.get('userType') == 'visitor']
            print(f"Total user: {total_user} | Visitors: {len(visitor_users)}")
            all_visitors.extend(visitor_users)
        return all_visitors
    except Exception as e:
        print(f"{ip_address} - {e}")
        return all_visitors


@contextmanager
def hikvision_session(ip_address: str, username: str, password: str):
    """Avtomatik session management"""
    session = requests.Session()
    session.auth = HTTPDigestAuth(username, password)
    try:
        yield session
    finally:
        session.close()


def delete_all_visitors_clean(ip_address: str, username: str, password: str):
    """Clean versiya - context manager bilan"""
    with hikvision_session(ip_address, username, password) as session:
        # 1. Search
        users = get_all_visitors(ip_address=ip_address, session=session)

        if not users:
            print("No visitors found")
            return

    with hikvision_session(ip_address, username, password) as session:
        # 2. Delete (xuddi shu session bilan)
        delete_url = f"http://{ip_address}/ISAPI/AccessControl/UserInfo/Delete?format=json"
        payload = {"UserInfoDelCond": {"EmployeeNoList": users}}

        res = session.put(url=delete_url, json=payload, timeout=10)
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text}")

    # Bu yerda avtomatik session.close() bo'ladi


delete_all_visitors_clean('192.0.0.64', 'admin', 'Dtm@13579')