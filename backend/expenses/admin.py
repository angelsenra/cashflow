from django.contrib import admin

from expenses.models import Category, Expense, Project


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 0


class CategoryAdmin(admin.ModelAdmin):
    inlines = [CategoryInline]
    search_fields = ["name"]


admin.site.register(Project)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Expense)
