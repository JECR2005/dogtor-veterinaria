#!/usr/bin/env bash
# S0-06 · Protege main y develop en GitHub: nada entra sin pull request con la integración continua
# («pruebas») en verde, y no se puede reescribir ni borrar el historial de esas ramas.
#
# Uso:  bash scripts/proteger_ramas.sh USUARIO/repositorio [APROBACIONES]
#   APROBACIONES = revisiones aprobadas requeridas en cada PR (por defecto 1).
#   Con un equipo de una sola persona en GitHub use 0 (decisión D-14): GitHub no deja aprobar el PR propio.
# Requisitos: gh autenticado con permisos de administrador del repositorio.
set -euo pipefail

REPO="${1:?Indica el repositorio: USUARIO/repositorio}"
APROBACIONES="${2:-1}"

for RAMA in main develop; do
  echo "Protegiendo ${RAMA} (aprobaciones requeridas: ${APROBACIONES})..."
  gh api -X PUT "repos/${REPO}/branches/${RAMA}/protection" \
    -H "Accept: application/vnd.github+json" \
    --input - <<JSON
{
  "required_status_checks": { "strict": false, "contexts": ["pruebas"] },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": ${APROBACIONES},
    "dismiss_stale_reviews": true
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
done
echo "Listo: main y develop protegidas."
