from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms

from expenses.models import Expense


class A(forms.DateTimeInput):
    input_type = "datetime-local"


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["spent_at", "amount", "source", "category", "notes"]
        widgets = {
            "spent_at": A(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Save"))
