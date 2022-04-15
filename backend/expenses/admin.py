from django.contrib import admin

from .models import Expense, Category, Priority


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 0


class PriorityAdmin(admin.ModelAdmin):
    inlines = [CategoryInline]
    search_fields = ['name']


admin.site.register(Priority, PriorityAdmin)
admin.site.register(Expense)
