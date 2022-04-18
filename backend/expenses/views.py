import datetime
import logging
import typing
from dataclasses import dataclass

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone

from auth.models import User
from expenses.forms import ExpenseForm, ProjectCreateForm
from expenses.models import Category, Expense, Project

logger = logging.getLogger(__name__)

DATE_FORMAT = "%Y-%m-%d"


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
    value_rows = _generate_value_rows(project=project)

    return render(
        request, "expenses/project_detail.html", dict(header_rows=header_rows, value_rows=value_rows, project=project)
    )


@login_required
def expense_list(request: AuthenticatedHttpRequest, project_public_id: str):
    project = get_object_or_404(Project.objects.filter(user=request.user), public_id=project_public_id)
    base_filter_args = [Q(category__project=project)]
    arg_category = request.GET.get("category")
    arg_show_children = request.GET.get("show_children")
    if arg_category:
        if arg_show_children and arg_show_children.lower() == "true":
            base_filter_args.append(Q(category__public_id=arg_category) | Q(category__parent__public_id=arg_category))
        else:
            base_filter_args.append(Q(category__public_id=arg_category))
    arg_from = request.GET.get("from")
    from_datetime = None
    if arg_from:
        from_datetime = datetime.datetime.strptime(arg_from, DATE_FORMAT)
    arg_to = request.GET.get("to")
    to_datetime = None
    if arg_to:
        to_datetime = datetime.datetime.strptime(arg_to, DATE_FORMAT)

    periods_expenses = list()
    periods = _generate_periods(amount=6, from_datetime=from_datetime, to_datetime=to_datetime)
    for period_start, period_end in periods:
        filter_kwargs = dict(
            spent_at__gte=from_datetime if from_datetime and from_datetime > period_start else period_start,
            spent_at__lt=to_datetime if to_datetime and to_datetime < period_end else period_end,
        )
        expenses = Expense.objects.filter(*base_filter_args, **filter_kwargs).order_by("spent_at").all()
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


@dataclass
class Header:
    name: str
    colspan: int
    rowspan: int
    category: Category
    is_total: bool

    @property
    def color(self):
        return self.category.color

    @property
    def link(self):
        return (
            reverse("expenses:expense_list", kwargs=dict(project_public_id=self.category.project.public_id))
            + f"?category={self.category.public_id}"
            + ("&show_children=True" if self.is_total else "")
        )


def _generate_header_rows(*, project: Project) -> list[list[Header]]:
    levels = Category.build_levels(None, project=project)
    parents_considered = list()
    header_rows = list()
    for a, level in enumerate(levels):
        levels_left = len(levels) - a
        header_row = list()
        for category, has_children in level:
            parent = category.parent
            if parent and parent not in parents_considered:
                header_row.append(Header(name="∑", colspan=1, rowspan=levels_left, category=parent, is_total=True))

            if has_children:
                columns_under_category = sum(
                    len(level_) + len([has_children for _, has_children in level_ if has_children])
                    for level_ in category.build_levels()
                )
                header_row.append(
                    Header(
                        name=category.name, colspan=columns_under_category, rowspan=1, category=category, is_total=True
                    )
                )
            else:
                header_row.append(
                    Header(name=category.name, colspan=1, rowspan=levels_left, category=category, is_total=False)
                )

            if parent:
                parents_considered.append(parent)
                if parent.children.count() == parents_considered.count(parent):
                    header_row.append(
                        Header(name="Other", colspan=1, rowspan=levels_left, category=parent, is_total=False)
                    )
        header_rows.append(header_row)
    return header_rows


@dataclass
class Period:
    project: Project
    period_start: datetime.datetime
    period_end: datetime.datetime

    @property
    def name(self):
        return self.period_start.strftime("%b %Y")

    @property
    def link(self):
        period_start_str = self.period_start.strftime(DATE_FORMAT)
        period_end_str = self.period_end.strftime(DATE_FORMAT)
        return (
            reverse("expenses:expense_list", kwargs=dict(project_public_id=self.project.public_id))
            + f"?from={period_start_str}&to={period_end_str}"
        )


@dataclass
class Value:
    amount: float
    category: typing.Optional[Category]
    period_start: datetime.datetime
    period_end: datetime.datetime
    is_total: bool

    @property
    def name(self):
        return "%.2f€" % self.amount

    @property
    def link(self):
        if self.category is None:
            return ""

        period_start_str = self.period_start.strftime(DATE_FORMAT)
        period_end_str = self.period_end.strftime(DATE_FORMAT)
        return (
            reverse("expenses:expense_list", kwargs=dict(project_public_id=self.category.project.public_id))
            + f"?category={self.category.public_id}&from={period_start_str}&to={period_end_str}"
            + ("&show_children=True" if self.is_total else "")
        )


def _generate_value_rows(*, project: Project) -> list[tuple[Period, list[Value]]]:
    value_rows = list()
    periods = _generate_periods(amount=6)
    for period_start, period_end in periods:
        filter_ = dict(spent_at__gte=period_start, spent_at__lte=period_end)
        values = Category.build_values(None, filter_=filter_, project=project)
        value_rows.append(
            (
                Period(project=project, period_start=period_start, period_end=period_end),
                [
                    Value(
                        amount=value,
                        category=category,
                        period_start=period_start,
                        period_end=period_end,
                        is_total=is_total,
                    )
                    for value, is_total, category in values
                ],
            )
        )
    return value_rows


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


def _generate_periods(
    *, amount: int, from_datetime: datetime.datetime = None, to_datetime: datetime.datetime = None
) -> list[tuple[datetime.datetime, datetime.datetime]]:
    ending_at = to_datetime or timezone.now()
    ending_at_months = ending_at.month - 1 + ending_at.year * 12 + 1
    if from_datetime:
        starting_at_months = from_datetime.month - 1 + from_datetime.year * 12
    else:
        starting_at_months = ending_at_months - amount

    return [
        (_get_datetime_from_month_total(m), _get_datetime_from_month_total(m + 1))
        for m in range(starting_at_months, ending_at_months)
    ]


def _get_datetime_from_month_total(month_total: int, /):
    return datetime.datetime(year=month_total // 12, month=month_total % 12 + 1, day=1)
