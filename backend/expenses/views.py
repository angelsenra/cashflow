import datetime
import logging
import typing

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone

from auth.models import User
from expenses.forms import ExpenseForm, ProjectCreateForm
from expenses.models import Category, Expense, Project

logger = logging.getLogger(__name__)


class AuthenticatedHttpRequest(HttpRequest):
    user: User


@login_required
def project_list(request: AuthenticatedHttpRequest):
    projects = sorted(request.user.projects.all(), key=lambda p: p.order)
    return render(request, "expenses/project_list.html", dict(projects=projects))


@login_required
def project_create(request: AuthenticatedHttpRequest):
    if request.method == "POST":
        form = ProjectCreateForm(request.POST)
        if form.is_valid():
            new_project = Project(
                user=request.user,
                name=form.cleaned_data["name"],
                notes=form.cleaned_data["notes"],
            )
            new_project.save()

            category_template = form.cleaned_data["category_template"]
            _create_categories_from_template(category_template, project=new_project)

            return HttpResponseRedirect(reverse("expenses:project_list"))
    else:
        form = ProjectCreateForm()

    return render(request, "expenses/project_create.html", dict(form=form))


@login_required
def project_detail(request: AuthenticatedHttpRequest, project_public_id: str):
    project = get_object_or_404(Project.objects.filter(user=request.user), public_id=project_public_id)
    header_rows = _generate_header_rows(project=project)
    value_rows = list()
    periods = _generate_periods(amount=6)
    for period_start, period_end in periods:
        filter_ = dict(spent_at__gte=period_start, spent_at__lte=period_end)
        values = Category.build_values(None, filter_=filter_, project=project)
        value_rows.append([period_start.strftime("%b %Y"), ["%.2f€" % value for value, _ in values]])

    return render(
        request, "expenses/project_detail.html", dict(header_rows=header_rows, value_rows=value_rows, project=project)
    )


@login_required
def expense_list(request: AuthenticatedHttpRequest, project_public_id: str):
    project = get_object_or_404(Project.objects.filter(user=request.user), public_id=project_public_id)
    periods_expenses = list()
    periods = _generate_periods(amount=6)
    for period_start, period_end in periods:
        expenses = (
            Expense.objects.filter(spent_at__gte=period_start, spent_at__lte=period_end, category__project=project)
            .order_by("spent_at")
            .all()
        )
        if not expenses:
            continue
        period_expenses = list()
        for a, expense in enumerate(expenses):
            period_expenses.append(dict(number=a + 1, expense=expense, expense_amount="%.2f€" % expense.amount))
        periods_expenses.append(dict(period_name=period_start.strftime("%b %Y"), period_expenses=period_expenses))

    return render(request, "expenses/expense_list.html", dict(periods_expenses=periods_expenses, project=project))


@login_required
def expense_detail(request: AuthenticatedHttpRequest, project_public_id: str, expense_public_id: str):
    project = get_object_or_404(Project.objects.filter(user=request.user), public_id=project_public_id)
    expense = get_object_or_404(Expense, public_id=expense_public_id, category__project=project)
    if request.method == "POST":
        form = ExpenseForm(request.POST, project=project, can_delete=True)
        if form.data.get("delete") == "Delete":
            expense.delete()
            return HttpResponseRedirect(
                reverse("expenses:expense_list", kwargs=dict(project_public_id=project.public_id))
            )
        if form.is_valid():
            expense.spent_at = form.cleaned_data["spent_at"]
            expense.amount = form.cleaned_data["amount"]
            expense.source = form.cleaned_data["source"]
            expense.category = form.cleaned_data["category"]
            expense.notes = form.cleaned_data["notes"]
            expense.save()
            return HttpResponseRedirect(
                reverse("expenses:expense_list", kwargs=dict(project_public_id=project.public_id))
            )
    else:
        form = ExpenseForm(instance=expense, project=project, can_delete=True)

    return render(request, "expenses/expense_detail.html", dict(form=form, project=project))


@login_required
def expense_create(request: AuthenticatedHttpRequest, project_public_id: str):
    project = get_object_or_404(Project.objects.filter(user=request.user), public_id=project_public_id)
    if request.method == "POST":
        form = ExpenseForm(request.POST, project=project, can_delete=False)
        if form.is_valid():
            new_expense = Expense(
                spent_at=form.cleaned_data["spent_at"],
                amount=form.cleaned_data["amount"],
                source=form.cleaned_data["source"],
                category=form.cleaned_data["category"],
                notes=form.cleaned_data["notes"],
            )
            new_expense.save()
            return HttpResponseRedirect(
                reverse("expenses:expense_list", kwargs=dict(project_public_id=project.public_id))
            )
    else:
        form = ExpenseForm(initial=dict(spent_at=timezone.now()), project=project, can_delete=False)

    return render(request, "expenses/expense_detail.html", dict(form=form, project=project))


def _generate_header_rows(project: Project) -> list[list[tuple[str, int, int, typing.Any]]]:
    levels = Category.build_levels(None, project=project)
    parents_considered = list()
    header_rows = list()
    for a, level in enumerate(levels):
        levels_left = len(levels) - a
        header_row = list()
        for category, has_children in level:
            parent = category.parent
            if parent and parent not in parents_considered:
                header_row.append(("∑", 1, levels_left, parent.color))

            if has_children:
                columns_under_category = sum(
                    len(level_) + len([has_children for _, has_children in level_ if has_children])
                    for level_ in category.build_levels()
                )
                header_row.append((category.name, columns_under_category, 1, category.color))
            else:
                header_row.append((category.name, 1, levels_left, category.color))

            if parent:
                parents_considered.append(parent)
                if parent.children.count() == parents_considered.count(parent):
                    header_row.append(("Other", 1, levels_left, parent.color))
        header_rows.append(header_row)
    return header_rows


def _create_categories_from_template(category_template: str, /, *, project: Project):
    BLUE = "#247BA0"
    GREEN = "#70C1B3"
    GREY = "#50514F"
    RED = "#F25F5C"
    YELLOW = "#FFE066"

    if category_template == "standard":
        income = Category(project=project, name="Income", color=GREEN)
        income.save()
        mandatory = Category(project=project, name="Mandatory", color=RED)
        mandatory.save()
        prioritary = Category(project=project, name="Prioritary", color=BLUE)
        prioritary.save()
        discretionary = Category(project=project, name="Discretionary", color=YELLOW)
        discretionary.save()
        investments = Category(project=project, name="Investments", color=GREY)
        investments.save()
    else:
        raise NotImplementedError(f"{category_template=}")


def _generate_periods(*, amount: int) -> list[tuple[datetime.datetime, datetime.datetime]]:
    now = timezone.now()
    month_total = now.month - 1 + now.year * 12
    return [
        (_get_datetime_from_month_total(month_total - i), _get_datetime_from_month_total(month_total - i + 1))
        for i in range(amount - 1, -1, -1)
    ]


def _get_datetime_from_month_total(month_total: int, /):
    return datetime.datetime(year=month_total // 12, month=month_total % 12 + 1, day=1)
