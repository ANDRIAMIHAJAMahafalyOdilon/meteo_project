from django.shortcuts import render
from .models import RechercheHistorique
from .services import WeatherService, VilleIntrouvableError, WeatherServiceError


def index(request):
    """Page d'accueil : formulaire de recherche d'une ville."""
    contexte = {}

    if request.method == "POST":
        ville = request.POST.get("ville", "").strip()

        if not ville:
            contexte["erreur"] = "Merci de saisir le nom d'une ville."
            return render(request, "meteo/index.html", contexte)

        try:
            service = WeatherService()
            meteo = service.get_meteo_actuelle(ville)
            previsions = service.get_previsions(ville, jours=3)

            # Sauvegarde dans l'historique (SQLite)
            RechercheHistorique.objects.create(
                ville=meteo["ville"],
                pays=meteo["pays"],
                temperature=meteo["temperature"],
                humidite=meteo["humidite"],
                vent=meteo["vent"],
                description=meteo["description"],
                icone_url=meteo["icone_url"],
            )

            contexte["meteo"] = meteo
            contexte["previsions"] = previsions

        except VilleIntrouvableError:
            contexte["erreur"] = f"Ville introuvable : « {ville} ». Vérifie l'orthographe."
        except WeatherServiceError as exc:
            contexte["erreur"] = f"Une erreur est survenue : {exc}"

    return render(request, "meteo/index.html", contexte)


def historique(request):
    """Affiche l'historique des recherches sauvegardées en base."""
    recherches = RechercheHistorique.objects.all()[:50]
    return render(request, "meteo/historique.html", {"recherches": recherches})