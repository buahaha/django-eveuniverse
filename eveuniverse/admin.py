from django.contrib import admin

from .models import EveSolarSystem, EveType, EveGroup, EveCategory


class EveUniverseEntityModelAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


@admin.register(EveCategory)
class EveCategoryAdmin(EveUniverseEntityModelAdmin):
    pass


@admin.register(EveGroup)
class EveGroupAdmin(EveUniverseEntityModelAdmin):
    pass


@admin.register(EveSolarSystem)
class EveSolarSystemAdmin(EveUniverseEntityModelAdmin):
    ordering = ["name"]
    search_fields = ["name"]


@admin.register(EveType)
class EveTypeAdmin(EveUniverseEntityModelAdmin):
    pass
