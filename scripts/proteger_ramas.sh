#!/usr/bin/env bash
# S0-06 · Protege main y develop en GitHub: solo se integra por pull request con una aprobación
# y con la integración continua en verde. Justificación: revisión entre pares al 100 % (Tabla 3.20).
#
# Uso:  bash scripts/proteger_ramas.sh USUARIO/dogtor
# Requisitos: gh autenticado con permisos de administrador del repositorio.
# Nota: en repositorios privados de cuentas gratuitas, GitHub no permite reglas de protección;
# en ese caso, hagan el repositorio público (sin datos reales) o usen GitHub Education.
set -euo pipefail

REPO="${1:?Indica el repositorio: USUARIO/dogtor}"

for RAMA in main develop; do
  echo "Protegiendo ${RAMA}..."
  gh api -X PUT "repos/${REPO}/branches/${RAMA}/protection" \
    -H "Accept: application/vnd.github+json" \
    --input - <<JSON
{
  "required_status_checks": { "strict": true, "contexts": ["pruebas"] },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
done
echo "Listo: main y develop solo aceptan pull requests revisados con CI en verde."
