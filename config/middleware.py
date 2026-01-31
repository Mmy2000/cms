from django.http import HttpResponseForbidden
from stamps.tasks import send_email
from django.conf import settings
import requests
from site_settings.models import AdminAllowedIP
from django.core.cache import cache
import logging
import ipaddress
from datetime import datetime

logger = logging.getLogger(__name__)

CACHE_KEY = "admin_allowed_ips"
CACHE_TIMEOUT = 60 * 5  # 5 minutes


class AdminIPRestrictionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def is_private_ip(self, ip):
        """Check if IP is private/local"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved
        except ValueError:
            return False

    def get_ip_info(self, ip):
        """Gather detailed information about the IP address with caching and fallback"""
        # Check if it's a private/local IP
        if self.is_private_ip(ip):
            return {
                "ip": ip,
                "geolocation": {
                    "country": "Local/Private Network",
                    "city": "N/A",
                    "region": "N/A",
                    "isp": "Private Network",
                    "org": "Reserved IP Range",
                    "timezone": "N/A",
                },
            }

        # Check cache first (cache for 24 hours to avoid rate limits)
        cache_key = f"ip_info_{ip}"
        cached_info = cache.get(cache_key)
        if cached_info:
            return cached_info

        info = {
            "ip": ip,
            "geolocation": None,
        }

        # Try multiple services with fallback
        services = [
            {
                "name": "ip-api.com",
                "url": f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query",
                "parser": self._parse_ipapi,
            },
            {
                "name": "ipinfo.io",
                "url": f"https://ipinfo.io/{ip}/json",
                "parser": self._parse_ipinfo,
            },
        ]

        for service in services:
            try:
                response = requests.get(service["url"], timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    parsed = service["parser"](data)
                    if parsed:
                        info["geolocation"] = parsed
                        # Cache for 24 hours
                        cache.set(cache_key, info, 86400)
                        logger.info(
                            f"Successfully retrieved IP info from {service['name']}"
                        )
                        break
            except Exception as e:
                logger.warning(
                    f"Failed to get IP info from {service['name']}: {str(e)}"
                )
                continue

        # If all services failed
        if not info["geolocation"]:
            info["geolocation"] = "Service unavailable"

        return info

    def _parse_ipapi(self, data):
        """Parse ip-api.com response"""
        if data.get("status") == "success":
            return {
                "country": data.get("country") or "Unknown",
                "city": data.get("city") or "Unknown",
                "region": data.get("regionName") or "Unknown",
                "isp": data.get("isp") or "Unknown",
                "org": data.get("org")
                or data.get("as")
                or "Unknown",  # Fallback to AS if org is empty
                "timezone": data.get("timezone") or "Unknown",
                "lat": data.get("lat"),
                "lon": data.get("lon"),
            }
        # Handle failure cases (private IPs, etc.)
        elif data.get("status") == "fail":
            logger.info(f"IP lookup failed: {data.get('message')}")
        return None

    def _parse_ipinfo(self, data):
        """Parse ipinfo.io response"""
        # ipinfo.io returns 'bogon' for private IPs or 'error' field for errors
        if "error" not in data and not data.get("bogon"):
            return {
                "country": data.get("country") or "Unknown",
                "city": data.get("city") or "Unknown",
                "region": data.get("region") or "Unknown",
                "isp": data.get("org") or "Unknown",
                "org": data.get("org") or "Unknown",
                "timezone": data.get("timezone") or "Unknown",
            }
        elif data.get("bogon"):
            logger.info(f"IP {data.get('ip')} is a bogon (private/reserved)")
        return None

    def get_client_ip(self, request):
        """Get the real client IP, considering proxies"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def __call__(self, request):
        if request.path.startswith(f"/{settings.ADMIN_URL}/"):
            ip = self.get_client_ip(request)
            ALLOWED_ADMIN_IPS = self._get_allowed_ips()

            if ip not in ALLOWED_ADMIN_IPS:
                # Gather comprehensive IP information
                ip_info = self.get_ip_info(ip)

                # Get additional request information
                user_agent = request.META.get("HTTP_USER_AGENT", "Unknown")
                referer = request.META.get("HTTP_REFERER", "Direct Access")
                request_method = request.method
                request_path = request.get_full_path()

                # Get current timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Get username if it's a POST request
                username = "Not attempted (viewing login page)"
                if request_method == "POST":
                    username = request.POST.get("username", "Not provided")

                # Format email message
                message = f"""
⚠️ UNAUTHORIZED ADMIN ACCESS ATTEMPT DETECTED

IP Address: {ip}

Geolocation Information:
{self._format_geolocation(ip_info['geolocation'])}

Request Details:
- Method: {request_method}
- Path: {request_path}
- User Agent: {user_agent}
- Referer: {referer}
- Timestamp: {timestamp}

Proxy/Forwarding Headers:
- X-Forwarded-For: {request.META.get('HTTP_X_FORWARDED_FOR', 'Not proxied')}
- X-Real-IP: {request.META.get('HTTP_X_REAL_IP', 'Not available')}

Login Information:
- Username: {username}

This is an automated security alert.
                """

                send_email.enqueue(
                    to_email=settings.DEFAULT_FROM_EMAIL,
                    first_name="Admin",
                    subject=f"⚠️ Unauthorized Admin Access from {ip} ({ip_info.get('geolocation', {}).get('country', 'Unknown') if isinstance(ip_info.get('geolocation'), dict) else 'Unknown'})",
                    message=message.strip(),
                )

                return HttpResponseForbidden("Access denied")

        return self.get_response(request)

    def _get_allowed_ips(self):
        """Fetch allowed admin IPs from the database or cache"""
        allowed_ips = cache.get(CACHE_KEY)
        if allowed_ips is None:
            allowed_ips = list(
                AdminAllowedIP.objects.filter(active=True).values_list(
                    "ip_address", flat=True
                )
            )
            cache.set(CACHE_KEY, allowed_ips, CACHE_TIMEOUT)
        return allowed_ips

    def _format_geolocation(self, geo):
        """Format geolocation data for email"""
        if isinstance(geo, dict):
            geo_info = f"""- Country: {geo.get('country', 'Unknown')}
- City: {geo.get('city', 'Unknown')}
- Region: {geo.get('region', 'Unknown')}
- ISP: {geo.get('isp', 'Unknown')}"""

            # Only add organization if it's different from ISP and not "Unknown"
            org = geo.get("org", "Unknown")
            if org != "Unknown" and org != geo.get("isp"):
                geo_info += f"\n- Organization: {org}"

            geo_info += f"\n- Timezone: {geo.get('timezone', 'Unknown')}"

            # Add coordinates if available
            if geo.get("lat") and geo.get("lon"):
                geo_info += f"\n- Coordinates: {geo.get('lat')}, {geo.get('lon')}"

            return geo_info
        return f"- {geo}"
