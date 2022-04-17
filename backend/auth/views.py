from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse


def account_profile(request: HttpRequest):
    return HttpResponseRedirect(reverse("expenses:index"))
