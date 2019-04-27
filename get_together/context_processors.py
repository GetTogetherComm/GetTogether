from django.conf import settings


def theme_engine(request):
    return {"theme": settings.THEME_CONFIG}
