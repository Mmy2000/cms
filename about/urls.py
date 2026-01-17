from .views import about_page
from django.urls import path
urlpatterns = [path("", about_page, name="about")]
