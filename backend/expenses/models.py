import itertools
import logging
import secrets
import typing
import uuid

from colorfield.fields import ColorField
from django.db import models

logger = logging.getLogger(__name__)


def generate_public_id():
    return secrets.token_urlsafe(9)


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(unique=True, default=generate_public_id, max_length=50, editable=False)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=200)
    order = models.IntegerField()
    color = ColorField(default="#FF0000")
    parent = models.ForeignKey("self", related_name="children", null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        if self.parent:
            return f"{self.name} (child of {self.parent.name})"
        else:
            return f"{self.name}"

    def build_levels(self: typing.Union["Category", None], iteration=0) -> list[list[tuple["Category", bool]]]:
        if iteration > 50:
            raise Exception(
                f"We hit 50 iterations on the recursive levels call. There might be something wrong with {self}"
            )

        if self is None:
            children = Category.objects.filter(parent=None).all()
            levels = list()
        else:
            children = self.children.all()
            levels = [[(self, bool(children))]]

        children_levels = [child.build_levels(iteration=iteration + 1) for child in children]
        if children_levels:
            for list_of_each_level in itertools.zip_longest(*children_levels):
                # zip_longest adds None if one of the children levels was shorter
                list_of_each_level = [i for i in list_of_each_level if i is not None]
                levels.append(list(itertools.chain(*list_of_each_level)))
        return levels

    def build_values(self: typing.Union["Category", None], iteration=0, filter_=None) -> list[tuple[float, bool]]:
        if filter_ is None:
            filter_ = dict()
        if iteration > 50:
            raise Exception(
                f"We hit 50 iterations on the recursive levels call. There might be something wrong with {self}"
            )

        if self is None:
            children = Category.objects.filter(parent=None).all()
            other = 0.0
        else:
            children = self.children.all()
            other = sum(expense.amount for expense in self.expenses.filter(**filter_).all())

        if not children:
            return [(other, False)]

        children_values = list(
            itertools.chain(*[child.build_values(iteration=iteration + 1, filter_=filter_) for child in children])
        )
        if self is None:
            return children_values
        return [
            (other + sum(value for value, is_total in children_values if not is_total), True),
            *children_values,
            (other, False),
        ]


class Expense(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(unique=True, default=generate_public_id, max_length=50, editable=False)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    spent_at = models.DateTimeField()
    amount = models.FloatField()
    source = models.CharField(max_length=200)
    category = models.ForeignKey(Category, related_name="expenses", on_delete=models.CASCADE)
    notes = models.CharField(max_length=1000, blank=True, null=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"${self.amount} at {self.source} on {self.spent_at} ({self.category})"
