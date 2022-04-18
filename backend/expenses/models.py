import itertools
import logging
import typing

from colorfield.fields import ColorField
from django.db import models

from auth.models import User
from helpers.models import BaseModel, generate_order

logger = logging.getLogger(__name__)


class Project(BaseModel):
    user = models.ForeignKey(User, related_name="projects", on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    order = models.IntegerField(default=generate_order)
    notes = models.CharField(max_length=1000, blank=True)

    def __str__(self):
        return f"Project {self.name}"


class Category(BaseModel):
    project = models.ForeignKey(Project, related_name="categories", on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    order = models.IntegerField(default=generate_order)
    color = ColorField(default="#FF0000")
    notes = models.CharField(max_length=1000, blank=True)
    parent = models.ForeignKey("self", related_name="children", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        if self.parent:
            return f"Category {self.name} (child of {self.parent.name})"
        else:
            return f"Category {self.name}"

    def build_levels(
        self: typing.Optional["Category"], iteration=0, project=None
    ) -> list[list[tuple["Category", bool]]]:
        if iteration > 50:
            raise Exception(
                f"We hit 50 iterations on the recursive levels call. There might be something wrong with {self}"
            )

        if self is None:
            children = Category.objects.filter(parent=None, project=project).all()
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

    def build_values(
        self: typing.Optional["Category"], iteration=0, filter_=None, project=None
    ) -> list[tuple[float, bool, typing.Optional["Category"]]]:
        if filter_ is None:
            filter_ = dict()
        if iteration > 50:
            raise Exception(
                f"We hit 50 iterations on the recursive levels call. There might be something wrong with {self}"
            )

        if self is None:
            children = Category.objects.filter(parent=None, project=project).all()
            other = 0.0
        else:
            children = self.children.all()
            other = sum(expense.amount for expense in self.expenses.filter(**filter_).all())

        if not children:
            return [(other, False, self)]

        children_values = list(
            itertools.chain(*[child.build_values(iteration=iteration + 1, filter_=filter_) for child in children])
        )
        if self is None:
            return children_values
        return [
            (other + sum(value for value, is_total, _ in children_values if not is_total), True, self),
            *children_values,
            (other, False, self),
        ]


class Expense(BaseModel):
    category = models.ForeignKey(Category, related_name="expenses", on_delete=models.CASCADE)
    spent_at = models.DateTimeField()
    amount = models.FloatField()
    source = models.CharField(max_length=200)
    notes = models.CharField(max_length=1000, blank=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Expense ${self.amount} at {self.source} on {self.spent_at} ({self.category})"
