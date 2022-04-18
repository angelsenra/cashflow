from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Submit
from django import forms

from expenses.models import Expense, Project


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
        widgets = {
            "spent_at": DatetimeLocalInput(),
        }

    def __init__(self, *args, can_delete, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.add_input(
            Button("cancel", "Cancel", css_class="btn btn-secondary", onclick="window.history.back()")
        )
        self.helper.add_input(Submit("submit", "Save"))
        if can_delete:
            self.helper.add_input(
                Button(
                    "delete",
                    "Delete",
                    css_class="btn btn-danger",
                    **{"data-toggle": "modal", "data-target": "#deleteModal"},
                )
            )
