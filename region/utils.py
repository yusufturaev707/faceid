from ipaddress import IPv4Address
import requests
import asyncio
from datetime import datetime, timedelta
import aiohttp
from django.db import transaction
from asgiref.sync import sync_to_async

from requests.auth import HTTPDigestAuth
headers = {"Content-Type": "application/json"}


def is_same_mac_addresses(base_url: str="") -> bool:
    api_url = f"{base_url}"
    return True

def is_check_healthy(ip_address: IPv4Address=None, mac_address:str=None, username: str=None, password: str=None) -> bool:
    auth = HTTPDigestAuth(username, password)
    api_url = f"http://{ip_address}/SDK/activateStatus"
    try:
        res = requests.get(api_url, auth=auth, timeout=10)
        if res.status_code == 200:
            print(res.text)
            if "<Activated>true</Activated>" in res.text:
                return True
            else:
                return False
        else:
            return False
    except requests.exceptions.ConnectionError as e:
        return False
    except Exception as e:
        print(f"{ip_address} - {e}")
        return False

def get_all_visitors(ip_address: IPv4Address=None, auth: HTTPDigestAuth = None) -> list:
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
        res = requests.post(url=api_url, auth=auth, json=payload, timeout=10)
        if res.status_code == 200:
            data = res.json()
            total_user = data.get('UserInfoSearch', {}).get('totalMatches', 0)
            all_users = data.get('UserInfoSearch', {}).get('UserInfo', [])
            visitor_users = [{"employeeNo": u.get('employeeNo')} for u in all_users if u.get('userType') == 'visitor']
            print(f"Total user: {total_user} | Normal users: {len(visitor_users)}")
            all_visitors.extend(visitor_users)
        return all_visitors
    except requests.exceptions.ConnectionError as e:
        print(f"{ip_address} - {e}")
        return all_visitors
    except Exception as e:
        print(f"{ip_address} - {e}")
        return all_visitors

def delete_all_visitors(ip_address: IPv4Address=None, mac_address:str=None, username: str=None, password: str=None):
    try:
        auth = HTTPDigestAuth(username, password)
        users = get_all_visitors(ip_address=ip_address, auth=auth)
        delete_url = f"http://{ip_address}/ISAPI/AccessControl/UserInfo/Delete?format=json&security=1"
        payload = {"UserInfoDelCond": {"EmployeeNoList": users}}
        res = requests.put(url=delete_url, auth=auth, json=payload, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data.get('statusCode') == 1:
                print("Success")
            else:
                print("Error")
        else:
            print("Error!")
    except Exception as e:
        print(f"{e}")


async def push_data_to_sbs():
    pass