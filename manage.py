#!/usr/bin/env python
"""Utilitaire en ligne de commande de Django."""
import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meteo_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Impossible d'importer Django. As-tu bien activé ton environnement "
            "virtuel et installé les dépendances (pip install -r requirements.txt) ?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()