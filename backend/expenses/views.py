import datetime
import typing

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from expenses.models import Category, Expense

MONTHNAMES = [None, "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def index(request):
    return HttpResponseRedirect(reverse("expenses:table"))


def table(request):
    header_rows = _generate_header_rows()
    value_rows = list()
    periods = _generate_periods()
    for period_start, period_end in periods:
        filter_ = dict(spent_at__gte=period_start, spent_at__lte=period_end)
        values = Category.build_values(None, filter_=filter_)
        value_rows.append(
            [f"{MONTHNAMES[period_start.month]}{period_start.year}", ["%.2f€" % value for value, _ in values]]
        )

    context = dict(header_rows=header_rows, value_rows=value_rows)
    return render(request, "expenses/table.html", context)


def list_(request):
    value_rows = list()
    for expense in Expense.objects.all():
        value_rows.append(
            (expense.spent_at.isoformat(), expense.amount, expense.category.name, expense.source, expense.notes)
        )
    context = dict(value_rows=value_rows)
    return render(request, "expenses/list.html", context)


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


def _generate_periods() -> list[tuple[datetime.datetime, datetime.datetime]]:
    now = timezone.now()
    month_total = now.month - 1 + now.year * 12
    return [
        (
            datetime.datetime(year=(month_total - i) // 12, month=(month_total - i) % 12 + 1, day=1),
            datetime.datetime(year=(month_total - i + 1) // 12, month=(month_total - i + 1) % 12 + 1, day=1),
        )
        for i in range(5, -1, -1)
    ]
