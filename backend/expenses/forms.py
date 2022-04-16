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
