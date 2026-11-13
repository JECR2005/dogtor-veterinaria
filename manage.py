#!/usr/bin/env python
"""Utilidad de línea de comandos de Django para el sistema Dogtor."""

import os
import sys
from pathlib import Path


def main():
    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).resolve().parent / ".env")
    except ImportError:
        pass
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. ¿Activaste el entorno virtual (.venv) "
            "e instalaste requirements-dev.txt?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
