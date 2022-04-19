import datetime

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Column, Div, Field, Layout, Row, Submit
from django import forms

from expenses.models import Category, Expense, Project


class DatetimeLocalInput(forms.DateTimeInput):
    input_type = "datetime-local"


class ProjectCreateForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "notes"]

    category_template = forms.ChoiceField(choices=[("standard", "Standard")])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.add_input(
            Button("cancel", "Cancel", css_class="btn btn-secondary", onclick="window.history.back()")
        )
        self.helper.add_input(Submit("submit", "Create"))


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["spent_at", "amount", "source", "category", "notes"]
        widgets = dict(spent_at=DatetimeLocalInput())

    def __init__(self, *args, project, initial=None, **kwargs):
        if initial is None:
            initial = dict()
        if "spent_at" not in initial:
            initial["spent_at"] = datetime.datetime.now()
        initial["spent_at"] = initial["spent_at"].replace(second=0)
        super().__init__(*args, initial=initial, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(project=project).order_by("order")
        self.fields["category"].label_from_instance = lambda c: c.name
        self.fields["category"].empty_label = None


class UpdateExpenseForm(ExpenseForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.add_input(
            Button("cancel", "Cancel", css_class="btn btn-secondary", onclick="window.history.back()")
        )
        self.helper.add_input(Submit("submit", "Update"))
        self.helper.add_input(
            Button(
                "delete",
                "Delete",
                css_class="btn btn-danger",
                **{"data-toggle": "modal", "data-target": "#deleteModal"},
            )
        )


class CreateExpenseFormInline(ExpenseForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            Row(
                Column(
                    Field("source", placeholder="e.g. McDonalds", size=20),
                    css_class="col-12 col-sm col-xl-auto order-1",
                ),
                Column("category", css_class="col-12 col-sm-auto mr-xl-auto order-2"),
                Column(css_class="col d-none order-3 order-lg-5"),
                Div(css_class="w-100 order-4"),
                Column("spent_at", css_class="col-12 col-md-auto order-5 order-md-6 order-lg-3"),
                Column(css_class="col d-none order-6 order-md-8"),
                Div(css_class="w-100 order-7"),
                Column(
                    Field("amount", placeholder="e.g. 123.45", size=7, css_class="text-right"),
                    css_class="col-12 col-sm-4 col-md-auto mr-md-auto order-8 order-md-5 order-lg-9",
                ),
                Column(
                    Field("notes", placeholder="(optional) e.g. I ordered every single burger on the menu."),
                    css_class="col-12 col-sm-8 col-md order-9 order-md-10",
                ),
                Column(
                    Submit("submit", "Create expense", css_class="btn btn-primary btn-block"),
                    css_class="col-12 col-sm-auto order-10 order-md-9 order-lg-8",
                ),
            ),
        )
