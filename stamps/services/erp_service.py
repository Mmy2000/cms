import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class ERPNextClient:
    def __init__(self):
        self.base_url = settings.ERPNEXT_URL.rstrip("/")
        self.headers = {
            "Authorization": f"token {settings.ERPNEXT_API_KEY}:{settings.ERPNEXT_API_SECRET}",
            "Content-Type": "application/json",
        }

    def create(self, doctype, data):
        """Create a new document in ERPNext"""
        url = f"{self.base_url}/api/resource/{doctype}"
        try:
            response = requests.post(url, json=data, headers=self.headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            logger.debug(f"ERPNext create response: {result}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"ERPNext create request failed: {str(e)}")
            raise

    def update_by_django_id(self, doctype, django_id, data):
        """Update an existing document in ERPNext by Django ID"""
        url = f"{self.base_url}/api/method/cms_django.api.stamps.update_stamp_by_django_id"
        payload = {
            "stamp_type": doctype,
            "django_id": django_id,
            "data": data,
        }
        try:
            response = requests.post(
                url, json=payload, headers=self.headers, timeout=10
            )
            response.raise_for_status()
            result = response.json()
            logger.debug(f"ERPNext update response: {result}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"ERPNext update request failed: {str(e)}")
            raise

    def delete_by_django_id(self, doctype, django_id):
        """Delete a document from ERPNext by Django ID"""
        url = f"{self.base_url}/api/method/cms_django.api.stamps.delete_stamp_by_django_id"
        payload = {
            "stamp_type": doctype,
            "django_id": django_id,
        }
        try:
            response = requests.post(
                url, json=payload, headers=self.headers, timeout=10
            )
            response.raise_for_status()
            result = response.json()
            logger.debug(f"ERPNext delete response: {result}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"ERPNext delete request failed: {str(e)}")
            raise
