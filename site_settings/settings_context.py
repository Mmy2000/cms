from .models import SiteConfiguration

def site_config_context(request):
    """
    Context processor to add site configuration to templates.
    """
    config = SiteConfiguration.objects.first()
    return {
        "site_configuration": config
    }