from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_POST
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
            previsions = service.get_previsions(
                meteo["latitude"], meteo["longitude"], meteo["timezone"], jours=7
            )

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
            contexte["previsions"] = previsions["jours"]
            contexte["previsions_horaires"] = previsions["heures"]

        except VilleIntrouvableError:
            contexte["erreur"] = f"Ville introuvable : « {ville} ». Vérifie l'orthographe."
        except WeatherServiceError as exc:
            contexte["erreur"] = f"Une erreur est survenue : {exc}"

    return render(request, "meteo/index.html", contexte)


def historique(request):
    """Affiche l'historique des recherches sauvegardées en base."""
    page_obj = Paginator(RechercheHistorique.objects.all(), 10).get_page(
        request.GET.get("page")
    )
    return render(request, "meteo/historique.html", {
        "page_obj": page_obj,
        "recherches": page_obj.object_list,
    })


def detail_historique(request, recherche_id):
    """Affiche les conditions météo enregistrées lors d'une recherche passée."""
    recherche = get_object_or_404(RechercheHistorique, pk=recherche_id)
    return render(request, "meteo/detail_historique.html", {"recherche": recherche})


@require_POST
def supprimer_historique(request, recherche_id):
    """Supprime une recherche sélectionnée depuis la page d'historique."""
    recherche = get_object_or_404(RechercheHistorique, pk=recherche_id)
    recherche.delete()
    try:
        page = max(1, int(request.POST.get("page", 1)))
    except (TypeError, ValueError):
        page = 1
    return HttpResponseRedirect(f"{reverse('historique')}?page={page}")
