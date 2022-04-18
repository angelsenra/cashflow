from django.contrib import admin

from expenses.models import Category, Expense, Project


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 0


class ProjectAdmin(admin.ModelAdmin):
    readonly_fields = ["public_id", "created_at", "updated_at", "id"]
    inlines = [CategoryInline]
    ordering = ["-created_at"]
    list_display = ["public_id", "user", "name", "created_at", "updated_at", "id"]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["public_id", "user__public_id", "name"]


class CategoryAdmin(admin.ModelAdmin):
    readonly_fields = ["public_id", "created_at", "updated_at", "id"]
    inlines = [CategoryInline]
    ordering = ["-created_at"]
    list_display = ["public_id", "project", "name", "created_at", "updated_at", "id"]
    list_filter = ["created_at", "project__public_id", "updated_at"]
    search_fields = ["name"]


admin.site.register(Project, ProjectAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Expense)
