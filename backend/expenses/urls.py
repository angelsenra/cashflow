from django.urls import path

from expenses.views import expense_create, expense_detail, expense_list, project_create, project_detail, project_list

app_name = "expenses"
urlpatterns = [
    path("", project_list, name="index"),
    path("", project_list, name="project_list"),
    path("projects/new/", project_create, name="project_create"),
    path("p/<str:project_public_id>/", project_detail, name="project_detail"),
    path("p/<str:project_public_id>/e/", expense_list, name="expense_list"),
    path("p/<str:project_public_id>/e/new/", expense_create, name="expense_create"),
    path("p/<str:project_public_id>/e/<str:expense_public_id>/", expense_detail, name="expense_detail"),
]
