from stamps.services.stamp_service import StampService
from .models import SiteConfiguration, Page, SEOSettings

def site_config_context(request):
    """
    Context processor to add site configuration to templates.
    """
    config = SiteConfiguration.objects.first()
    return {
        "site_configuration": config
    }


def seo_context(request):
    service = StampService()
    pages = Page.objects.filter(active=True)
    # Try to find matching Page using URL path
    page = Page.objects.filter(page_url=request.path).first()

    seo = None
    if page:
        seo = SEOSettings.objects.filter(page=page).first()

    stamps_this_month = StampService.get_this_month()
    total_pension= service.calculate_pension(service.get_queryset())

    return {
        "current_page": page,
        "seo": seo,
        "pages": pages,
        "stamps_this_month": stamps_this_month,
        "total_pension": total_pension,
    }
