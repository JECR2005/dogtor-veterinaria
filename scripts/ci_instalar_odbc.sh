#!/usr/bin/env bash
# Instala en el servidor de GitHub Actions (Ubuntu) el ODBC Driver 18 for SQL Server y sqlcmd (mssql-tools18).
# Las imágenes de GitHub a veces ya traen el repositorio de Microsoft o el controlador: no se repite lo que ya existe.
set -euo pipefail

if dpkg -s msodbcsql18 >/dev/null 2>&1 && [ -x /opt/mssql-tools18/bin/sqlcmd ]; then
  echo "ODBC Driver 18 y sqlcmd ya están instalados."
  exit 0
fi

sudo apt-get update -q
if ! apt-cache policy msodbcsql18 | grep -q "Candidate: [0-9]"; then
  echo "Agregando el repositorio de paquetes de Microsoft..."
  curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
    | sudo gpg --batch --yes --dearmor -o /usr/share/keyrings/microsoft-prod.gpg
  curl -fsSL "https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list" \
    | sudo tee /etc/apt/sources.list.d/mssql-release.list
  sudo apt-get update -q
fi
sudo ACCEPT_EULA=Y apt-get install -y -q msodbcsql18 mssql-tools18 unixodbc-dev
odbcinst -q -d
