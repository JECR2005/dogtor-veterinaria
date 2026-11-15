#!/usr/bin/env bash
# S1-15 · Copia Bootstrap, Bootstrap Icons y FullCalendar a static/vendor/ para que la interfaz funcione
# sin internet en el local (R07). Toma los paquetes oficiales de npm con versión fija y guarda sus licencias
# y la huella SHA-256 de cada archivo en static/vendor/VERSIONES.txt (registro de componentes, S0-04).
#
# Uso: bash scripts/traer_componentes.sh   (necesita npm e internet; lo ejecuta el flujo «Traer componentes»)
set -euo pipefail

BOOTSTRAP=5.3.3
ICONOS=1.11.3
FULLCALENDAR=6.1.15

raiz="$(cd "$(dirname "$0")/.." && pwd)"
destino="$raiz/static/vendor"
temporal="$(mktemp -d)"
trap 'rm -rf "$temporal"' EXIT

desempacar() {  # paquete@versión → carpeta
  local paquete="$1" carpeta="$temporal/$2"
  mkdir -p "$carpeta"
  (cd "$temporal" && npm pack --silent "$paquete" >/dev/null)
  tar -xzf "$temporal"/*.tgz -C "$carpeta" --strip-components=1
  rm "$temporal"/*.tgz
}

desempacar "bootstrap@$BOOTSTRAP" bootstrap
desempacar "bootstrap-icons@$ICONOS" iconos
desempacar "fullcalendar@$FULLCALENDAR" fullcalendar
desempacar "@fullcalendar/core@$FULLCALENDAR" fullcalendar-core

rm -rf "$destino"
mkdir -p "$destino"/bootstrap/{css,js} "$destino"/bootstrap-icons/fonts "$destino"/fullcalendar/locales

cp "$temporal/bootstrap/dist/css/bootstrap.min.css" "$destino/bootstrap/css/"
cp "$temporal/bootstrap/dist/js/bootstrap.bundle.min.js" "$destino/bootstrap/js/"
cp "$temporal/bootstrap/LICENSE" "$destino/bootstrap/LICENSE"

cp "$temporal/iconos/font/bootstrap-icons.min.css" "$destino/bootstrap-icons/"
cp "$temporal/iconos/font/fonts/bootstrap-icons.woff2" "$temporal/iconos/font/fonts/bootstrap-icons.woff" \
   "$destino/bootstrap-icons/fonts/"
cp "$temporal/iconos/LICENSE" "$destino/bootstrap-icons/LICENSE"

cp "$temporal/fullcalendar/index.global.min.js" "$destino/fullcalendar/"
cp "$temporal/fullcalendar-core/locales/es.global.min.js" "$destino/fullcalendar/locales/"
cp "$temporal/fullcalendar/LICENSE.md" "$destino/fullcalendar/LICENSE.md" 2>/dev/null \
  || cp "$temporal/fullcalendar-core/LICENSE.md" "$destino/fullcalendar/LICENSE.md"

# Quita la referencia a los mapas de depuración, que no se copian
sed -i '/sourceMappingURL=/d' "$destino/bootstrap/css/bootstrap.min.css" "$destino/bootstrap/js/bootstrap.bundle.min.js"

{
  echo "Componentes de terceros copiados por scripts/traer_componentes.sh (S1-15, R07)"
  echo "Bootstrap $BOOTSTRAP (MIT) · Bootstrap Icons $ICONOS (MIT) · FullCalendar $FULLCALENDAR estándar (MIT)"
  echo
  echo "SHA-256:"
  (cd "$destino" && find . -type f ! -name VERSIONES.txt | sort | xargs sha256sum)
} > "$destino/VERSIONES.txt"

cat "$destino/VERSIONES.txt"
