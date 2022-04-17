from django.urls import path

from expenses.views import create_expense, detail, list_, project_create, project_list, table

app_name = "expenses"
urlpatterns = [
    path("", project_list, name="index"),
    path("", project_list, name="project_list"),
    path("projects/new/", project_create, name="project_create"),
    path("p/4jl192o02/overview/?collapsed=828391,987298", table, name="table"),
    path("p/4jl192o02/expenses/?filter=yeo", list_, name="list"),
    path("p/4jl192o02/expenses/new/", create_expense, name="create_expense"),
    path("p/4jl192o02/expenses/<str:expense_public_id>/", detail, name="detail"),
]
