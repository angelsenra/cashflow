from django.contrib import admin

from .models import Category, Expense


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 0


class CategoryAdmin(admin.ModelAdmin):
    inlines = [CategoryInline]
    search_fields = ["name"]


admin.site.register(Category, CategoryAdmin)
admin.site.register(Expense)
