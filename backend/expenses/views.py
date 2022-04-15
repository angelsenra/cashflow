from itertools import zip_longest
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.http import HttpResponse
from .models import Category


def index(request):
    return HttpResponseRedirect(reverse("expenses:table"))


def table(request):
    category_list = Category.objects.order_by("order").all()

    levels, _ = Category.build_levels(None)
    parents_considered = list()
    header_rows = list()
    for a, level in enumerate(levels):
        levels_left = len(levels) - a
        header_row = list()
        for category, has_children in level:
            parent = category.parent
            if parent and parent not in parents_considered:
                header_row.append(["Total", 1, levels_left])
            _, columns_under_category = category.build_levels()
            header_row.append([category.name, columns_under_category, 1 if has_children else levels_left])
            if parent:
                parents_considered.append(parent)
                if parent.children.count() == parents_considered.count(parent):
                    header_row.append(["Other", 1, levels_left])
        header_rows.append(header_row)

    parents_considered = list()
    value_rows = list()
    value_rows.append(["Apr22", [value for value, _ in Category.build_values(None)]])
    value_rows.append(["May22", [0] * 13])
    value_rows.append(["Jun22", [1] * 13])

    context = {"category_list": category_list, "header_rows": header_rows, "value_rows": value_rows}
    return render(request, "expenses/table.html", context)
