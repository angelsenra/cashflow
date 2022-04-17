from django.urls import path

from . import views

app_name = "expenses"
urlpatterns = [
    path("", views.index, name="home"),
    path("", views.index, name="index"),
    path("p/4jl192o02/overview/?collapsed=828391,987298", views.table, name="table"),
    path("p/4jl192o02/expenses/?filter=yeo", views.list_, name="list"),
    path("p/4jl192o02/expenses/new/", views.create_expense, name="create_expense"),
    path("p/4jl192o02/expenses/<str:expense_public_id>/", views.detail, name="detail"),
]
