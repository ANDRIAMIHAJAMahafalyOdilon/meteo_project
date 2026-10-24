"""
Service responsable de la communication avec l'API externe WeatherAPI.
Toute la logique d'appel réseau est centralisée ici, pour respecter le
principe de séparation des responsabilités (les vues ne font qu'orchestrer).
"""
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
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

    def get_meteo_actuelle(self, ville: str) -> dict:
        """Récupère la météo actuelle avec un fournisseur de secours."""
        if not self.api_key:
            return self._get_meteo_open_meteo(ville)

        url = f"{BASE_URL}/current.json"
        params = {"key": self.api_key, "q": ville, "lang": "fr"}
        try:
            response = requests.get(url, params=params, timeout=5)
        except requests.exceptions.RequestException:
            return self._get_meteo_open_meteo(ville)

        if response.status_code == 400:
            raise VilleIntrouvableError(f"Ville introuvable : {ville}")
        if response.status_code == 429 or response.status_code >= 500:
            return self._get_meteo_open_meteo(ville)
        if response.status_code != 200:
            raise WeatherServiceError(
                f"Erreur API ({response.status_code}) : {response.text}"
            )

        return self._formater_reponse(response.json())

    def _get_meteo_open_meteo(self, ville: str) -> dict:
        """Utilise Open-Meteo si WeatherAPI est indisponible ou non configurée."""
        try:
            recherche = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": ville, "count": 1, "language": "fr", "format": "json"},
                timeout=8,
            )
            recherche.raise_for_status()
            resultats = recherche.json().get("results", [])
            if not resultats:
                raise VilleIntrouvableError(f"Ville introuvable : {ville}")

            lieu = resultats[0]
            reponse_meteo = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lieu["latitude"],
                    "longitude": lieu["longitude"],
                    "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                    "timezone": lieu.get("timezone", "auto"),
                },
                timeout=8,
            )
            reponse_meteo.raise_for_status()
            current = reponse_meteo.json().get("current", {})
            description, icone = self._condition_open_meteo(current.get("weather_code", -1))
            return {
                "ville": lieu.get("name", ville),
                "pays": lieu.get("country", ""),
                "latitude": lieu["latitude"],
                "longitude": lieu["longitude"],
                "timezone": lieu.get("timezone", "UTC"),
                "temperature": current.get("temperature_2m"),
                "humidite": current.get("relative_humidity_2m"),
                "vent": current.get("wind_speed_10m"),
                "description": description,
                "icone_url": "",
                "icone": icone,
            }
        except VilleIntrouvableError:
            raise
        except requests.exceptions.RequestException as exc:
            raise WeatherServiceError(
                "WeatherAPI ne répond pas et le service météo de secours est inaccessible. "
                "Vérifie ta connexion puis réessaie."
            ) from exc

    def get_previsions(self, latitude: float, longitude: float, timezone: str, jours: int = 7) -> dict:
        """Récupère les prévisions horaires et journalières sur sept jours."""
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "temperature_2m,weather_code",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min",
            "timezone": timezone or "auto",
            "forecast_days": jours,
        }

        try:
            response = requests.get(url, params=params, timeout=8)
        except requests.exceptions.RequestException as exc:
            raise WeatherServiceError(f"Erreur réseau : {exc}") from exc

        if response.status_code != 200:
            raise WeatherServiceError(
                f"Erreur API ({response.status_code}) : {response.text}"
            )

        data = response.json()
        daily = data.get("daily", {})
        previsions = []
        for index, jour in enumerate(daily.get("time", [])):
            description, icone = self._condition_open_meteo(daily["weather_code"][index])
            previsions.append({
                "date": datetime.strptime(jour, "%Y-%m-%d").date(),
                "temp_max": daily["temperature_2m_max"][index],
                "temp_min": daily["temperature_2m_min"][index],
                "description": description,
                "icone": icone,
            })

        heures = []
        hourly = data.get("hourly", {})
        if hourly.get("time"):
            heure_locale = datetime.now(ZoneInfo(data.get("timezone", timezone or "UTC")))
            for index, heure in enumerate(hourly["time"]):
                heure_prevue = datetime.fromisoformat(heure).replace(tzinfo=heure_locale.tzinfo)
                ecart_heures = heure_prevue.hour - heure_locale.hour
                if heure_prevue.date() == heure_locale.date() and ecart_heures >= 0 and ecart_heures % 5 == 0:
                    description, icone = self._condition_open_meteo(hourly["weather_code"][index])
                    heures.append({
                        "heure": heure_prevue.strftime("%H:%M"),
                        "temperature": hourly["temperature_2m"][index],
                        "description": description,
                        "icone": icone,
                    })

        return {"jours": previsions, "heures": heures}

    @staticmethod
    def _condition_open_meteo(code: int) -> tuple:
        """Mappe les codes WMO vers des conditions et icones."""
        if code == 0:
            return "Ciel dégagé", "\u2600\ufe0f"
        if code == 1:
            return "Majoritairement dégagé", "\U0001f324"
        if code == 2:
            return "Partiellement nuageux", "\u26c5"
        if code == 3:
            return "Couvert", "\u2601"
        if code in (45, 48):
            return "Brouillard", "\U0001f32b"
        if code in (51, 53, 55, 56, 57):
            return "Bruine", "\U0001f326"
        if code in (61, 63, 65, 66, 67, 80, 81, 82):
            return "Pluie", "\U0001f327"
        if code in (71, 73, 75, 77, 85, 86):
            return "Neige", "\U0001f328"
        if code in (95, 96, 99):
            return "Orage", "\U0001f329"
        return "Conditions variables", "\U0001f321"

    @staticmethod
    def _formater_reponse(data: dict) -> dict:
        """Transforme la réponse brute de l'API en dictionnaire simplifié."""
        location = data.get("location", {})
        current = data.get("current", {})
        condition = current.get("condition", {})

        return {
            "ville": location.get("name"),
            "pays": location.get("country"),
            "latitude": location.get("lat"),
            "longitude": location.get("lon"),
            "timezone": location.get("tz_id"),
            "temperature": current.get("temp_c"),
            "humidite": current.get("humidity"),
            "vent": current.get("wind_kph"),
            "description": condition.get("text"),
            "icone_url": "https:" + condition.get("icon", ""),
        }
