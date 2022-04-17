from django.urls import path

from auth.views import account_profile

app_name = "auth"
urlpatterns = [
    path("profile/", account_profile, name="account_profile"),
]
