# Reportes de OWASP ZAP (TS-02, S5-11)

`docker compose run --rm zap` escanea https://dogtor.local desde la red de Docker (D-25) y deja aquí:

- `zap_TS02.md`: resumen de alertas por riesgo (se sube al repositorio como evidencia).
- `zap_TS02.html`: reporte completo (no se sube; queda en la laptop).

El escaneo es `zap-full-scan` sin sesión: rastrea las páginas públicas (inicio de sesión) y les envía ataques
activos (scripts, inyección SQL, etc.). Las pantallas con sesión se cubren con las pruebas automáticas de
`tests/sistema/test_TS02_entradas_maliciosas.py`, que envían las mismas entradas maliciosas a todos los
buscadores y a los formularios con texto libre.
