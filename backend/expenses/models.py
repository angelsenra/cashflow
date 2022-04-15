import typing
import itertools
from django.db import models
from colorfield.fields import ColorField
import logging
import uuid

logger = logging.getLogger(__name__)

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=200)
    order = models.IntegerField()
    color = ColorField(default='#FF0000')
    parent = models.ForeignKey("self", related_name="children", null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        if self.parent:
            return f"{self.name} (child of {self.parent.name})"
        else:
            return f"{self.name}"

    def build_levels(self, iteration=0) -> tuple[list[list[tuple["Category", bool]]], int]:
        if iteration > 50:
            raise Exception(f"We hit 50 iterations on the recursive levels call. There might be something wrong with {self}")

        if self is None:
            children = Category.objects.filter(parent=None).all()
            levels = list()
        else:
            children = self.children.all()
            levels = [[(self, bool(children))]]

        children_levels = [c.build_levels(iteration=iteration + 1)[0] for c in children]
        if children_levels:
            for i in range(max([len(cl) for cl in children_levels])):
                li = list()
                for cl in children_levels:
                    if len(cl) <= i:
                        continue
                    li.extend(cl[i])
                levels.append(li)
        columns = sum(len(l) + len([i for i in l if i[1]]) for l in levels[::-1])
        return levels, columns

    def build_values(self, iteration=0) -> list[tuple[int, bool]]:
        if iteration > 50:
            raise Exception(f"We hit 50 iterations on the recursive levels call. There might be something wrong with {self}")

        if self is None:
            children = Category.objects.filter(parent=None).all()
            other = 0
        else:
            children = self.children.all()
            other = sum(expense.amount for expense in self.expenses.all())

        if not children:
            return [(other, False)]

        children_values = list(itertools.chain(*[child.build_values(iteration=iteration + 1) for child in children]))
        if self is None:
            return children_values
        return [(other + sum(v[0] for v in children_values if not v[1]), True), *children_values, (other, False)]


class Expense(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    amount = models.FloatField()
    source = models.CharField(max_length=200)
    spent_at = models.DateTimeField()
    category = models.ForeignKey(Category, related_name="expenses", on_delete=models.CASCADE)
    notes = models.CharField(max_length=1000, blank=True, null=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"${self.amount} at {self.source} on {self.spent_at} ({self.category})"
