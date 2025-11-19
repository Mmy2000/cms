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
    pages = Page.objects.all()
    # Try to find matching Page using URL path
    page = Page.objects.filter(page_url=request.path).first()

    seo = None
    if page:
        seo = SEOSettings.objects.filter(page=page).first()

    return {
        "current_page": page,
        "seo": seo,
        "pages": pages,
    }
