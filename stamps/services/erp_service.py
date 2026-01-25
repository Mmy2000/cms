import requests
from django.conf import settings


class ERPNextClient:
    def __init__(self):
        self.base_url = settings.ERPNEXT_URL.rstrip("/")
        self.headers = {
            "Authorization": f"token {settings.ERPNEXT_API_KEY}:{settings.ERPNEXT_API_SECRET}",
            "Content-Type": "application/json",
        }

    def create(self, doctype, data):
        url = f"{self.base_url}/api/resource/{doctype}"
        response = requests.post(url, json=data, headers=self.headers, timeout=10)
        response.raise_for_status()
        return response.json()

    def update_by_django_id(self, doctype, django_id, data):
        url = f"{self.base_url}/api/method/cms_django.api.stamps.update_stamp_by_django_id"
        payload = {
            "stamp_type": doctype,
            "django_id": django_id,
            "data": data,
        }
        response = requests.post(url, json=payload, headers=self.headers, timeout=10)
        response.raise_for_status()
        return response.json()

    def delete_by_django_id(self, doctype, django_id):
        url = f"{self.base_url}/api/method/cms_django.api.stamps.delete_stamp_by_django_id"
        payload = {
            "stamp_type": doctype,
            "django_id": django_id,
        }
        response = requests.post(url, json=payload, headers=self.headers, timeout=10)
        response.raise_for_status()
        return response.json()
