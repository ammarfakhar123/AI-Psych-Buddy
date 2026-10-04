from django.conf import settings


def wellness_disclaimer(request):
    """Makes {{ WELLNESS_DISCLAIMER }} available in every template."""
    return {"WELLNESS_DISCLAIMER": settings.WELLNESS_DISCLAIMER}
