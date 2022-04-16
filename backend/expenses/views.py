import datetime
import typing

from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone

from expenses.forms import ExpenseForm
from expenses.models import Category, Expense

MONTHNAMES = [None, "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def index(request: HttpRequest):
    return HttpResponseRedirect(reverse("expenses:table"))


def table(request: HttpRequest):
    header_rows = _generate_header_rows()
    value_rows = list()
    periods = _generate_periods(amount=6)
    for period_start, period_end in periods:
        filter_ = dict(spent_at__gte=period_start, spent_at__lte=period_end)
        values = Category.build_values(None, filter_=filter_)
        value_rows.append([period_start.strftime("%b %Y"), ["%.2f€" % value for value, _ in values]])

    context = dict(header_rows=header_rows, value_rows=value_rows)
    return render(request, "expenses/table.html", context)


def list_(request: HttpRequest):
    periods_expenses = list()
    periods = _generate_periods(amount=6)
    for period_start, period_end in periods:
        expenses = (
            Expense.objects.filter(spent_at__gte=period_start, spent_at__lte=period_end).order_by("spent_at").all()
        )
        if not expenses:
            continue
        period_expenses = list()
        for a, expense in enumerate(expenses):
            period_expenses.append(dict(number=a + 1, expense=expense, expense_amount="%.2f€" % expense.amount))
        periods_expenses.append(dict(period_name=period_start.strftime("%b %Y"), period_expenses=period_expenses))
    context = dict(periods_expenses=periods_expenses)
    return render(request, "expenses/list.html", context)


def detail(request: HttpRequest, expense_public_id: str):
    expense = get_object_or_404(Expense, public_id=expense_public_id)
    if request.method == "POST":
        form = ExpenseForm(request.POST, can_delete=True)
        if form.data.get("delete") == "Delete":
            expense.delete()
            return HttpResponseRedirect(reverse("expenses:list"))
        if form.is_valid():
            expense.spent_at = form.cleaned_data["spent_at"]
            expense.amount = form.cleaned_data["amount"]
            expense.source = form.cleaned_data["source"]
            expense.category = form.cleaned_data["category"]
            expense.notes = form.cleaned_data["notes"]
            expense.save()
            return HttpResponseRedirect(reverse("expenses:list"))
    else:
        form = ExpenseForm(instance=expense, can_delete=True)

    return render(request, "expenses/detail.html", dict(form=form))


def create_expense(request: HttpRequest):
    if request.method == "POST":
        form = ExpenseForm(request.POST, can_delete=False)
        if form.is_valid():
            new_expense = Expense(
                spent_at=form.cleaned_data["spent_at"],
                amount=form.cleaned_data["amount"],
                source=form.cleaned_data["source"],
                category=form.cleaned_data["category"],
                notes=form.cleaned_data["notes"],
            )
            new_expense.save()
            return HttpResponseRedirect(reverse("expenses:list"))
    else:
        form = ExpenseForm(initial=dict(spent_at=timezone.now()), can_delete=False)

    return render(request, "expenses/detail.html", dict(form=form))


def _generate_header_rows() -> list[list[tuple[str, int, int, typing.Any]]]:
    levels = Category.build_levels(None)
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


def _generate_periods(*, amount: int) -> list[tuple[datetime.datetime, datetime.datetime]]:
    now = timezone.now()
    month_total = now.month - 1 + now.year * 12
    return [
        (_get_datetime_from_month_total(month_total - i), _get_datetime_from_month_total(month_total - i + 1))
        for i in range(amount - 1, -1, -1)
    ]


def _get_datetime_from_month_total(month_total: int, /):
    return datetime.datetime(year=month_total // 12, month=month_total % 12 + 1, day=1)
