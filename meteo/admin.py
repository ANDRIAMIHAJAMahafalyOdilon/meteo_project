# pyrefly: ignore [missing-import]
from django.contrib import admin
from .models import RechercheHistorique


@admin.register(RechercheHistorique)
class RechercheHistoriqueAdmin(admin.ModelAdmin):
    list_display = ("ville", "pays", "temperature", "description", "date_recherche")
    list_filter = ("pays",)
    search_fields = ("ville",)