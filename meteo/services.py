"""
Service responsable de la communication avec l'API externe WeatherAPI.
Toute la logique d'appel réseau est centralisée ici, pour respecter le
principe de séparation des responsabilités (les vues ne font qu'orchestrer).
"""
import requests
from django.conf import settings


class VilleIntrouvableError(Exception):
    """Levée quand l'API ne trouve pas la ville demandée."""
    pass


class WeatherServiceError(Exception):
    """Levée pour toute autre erreur de communication avec l'API."""
    pass


BASE_URL = "https://api.weatherapi.com/v1"


class WeatherService:
    """Encapsule les appels à WeatherAPI (météo actuelle et prévisions)."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.WEATHER_API_KEY
        if not self.api_key:
            raise WeatherServiceError(
                "Aucune clé API configurée. Vérifie ton fichier .env "
                "(variable WEATHER_API_KEY)."
            )

    def get_meteo_actuelle(self, ville: str) -> dict:
        """
        Récupère la météo actuelle pour une ville donnée.
        Retourne un dictionnaire simplifié et lève une exception explicite
        en cas d'erreur.
        """
        url = f"{BASE_URL}/current.json"
        params = {"key": self.api_key, "q": ville, "lang": "fr"}

        try:
            response = requests.get(url, params=params, timeout=5)
        except requests.exceptions.RequestException as exc:
            raise WeatherServiceError(f"Erreur réseau : {exc}") from exc

        if response.status_code == 400:
            raise VilleIntrouvableError(f"Ville introuvable : {ville}")
        if response.status_code != 200:
            raise WeatherServiceError(
                f"Erreur API ({response.status_code}) : {response.text}"
            )

        data = response.json()
        return self._formater_reponse(data)

    def get_previsions(self, ville: str, jours: int = 3) -> list:
        """Récupère les prévisions sur plusieurs jours pour une ville."""
        url = f"{BASE_URL}/forecast.json"
        params = {"key": self.api_key, "q": ville, "days": jours, "lang": "fr"}

        try:
            response = requests.get(url, params=params, timeout=5)
        except requests.exceptions.RequestException as exc:
            raise WeatherServiceError(f"Erreur réseau : {exc}") from exc

        if response.status_code == 400:
            raise VilleIntrouvableError(f"Ville introuvable : {ville}")
        if response.status_code != 200:
            raise WeatherServiceError(
                f"Erreur API ({response.status_code}) : {response.text}"
            )

        data = response.json()
        previsions = []
        for jour in data.get("forecast", {}).get("forecastday", []):
            previsions.append({
                "date": jour["date"],
                "temp_max": jour["day"]["maxtemp_c"],
                "temp_min": jour["day"]["mintemp_c"],
                "description": jour["day"]["condition"]["text"],
                "icone_url": "https:" + jour["day"]["condition"]["icon"],
            })
        return previsions

    @staticmethod
    def _formater_reponse(data: dict) -> dict:
        """Transforme la réponse brute de l'API en dictionnaire simplifié."""
        location = data.get("location", {})
        current = data.get("current", {})
        condition = current.get("condition", {})

        return {
            "ville": location.get("name"),
            "pays": location.get("country"),
            "temperature": current.get("temp_c"),
            "humidite": current.get("humidity"),
            "vent": current.get("wind_kph"),
            "description": condition.get("text"),
            "icone_url": "https:" + condition.get("icon", ""),
        }