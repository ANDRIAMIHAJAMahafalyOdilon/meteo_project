from django.db import models


class RechercheHistorique(models.Model):
    """
    Représente une recherche météo effectuée, sauvegardée en base SQLite
    pour construire l'historique consultable par l'utilisateur.
    """
    ville = models.CharField(max_length=100)
    pays = models.CharField(max_length=100, blank=True)
    temperature = models.FloatField(help_text="Température en °C")
    humidite = models.IntegerField(help_text="Humidité en %")
    vent = models.FloatField(help_text="Vitesse du vent en km/h")
    description = models.CharField(max_length=200)
    icone_url = models.URLField(blank=True)
    date_recherche = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_recherche']
        verbose_name = "Recherche météo"
        verbose_name_plural = "Historique des recherches"

    def __str__(self):
        return f"{self.ville} - {self.date_recherche:%d/%m/%Y %H:%M}"