# Reportes de OWASP ZAP (TS-02, S5-11)

`docker compose run --rm zap` escanea https://dogtor.local desde la red de Docker (D-25) y deja aquí:

- `zap_TS02.md`: resumen de alertas por riesgo (se sube al repositorio como evidencia).
- `zap_TS02.html`: reporte completo (no se sube; queda en la laptop).

El escaneo es `zap-full-scan` sin sesión: rastrea las páginas públicas (inicio de sesión) y les envía ataques
activos (scripts, inyección SQL, plantillas, comandos, etc.). Las pantallas con sesión se cubren con las pruebas
automáticas de `tests/sistema/test_TS02_entradas_maliciosas.py`, que envían las mismas entradas maliciosas a
todos los buscadores y a los formularios con texto libre.

## Resultados (21/11/2026, JECR2005, ZAP 2.17.0)

| Escaneo | FAIL | WARN | PASS | Alto | Medio | Bajo | Informativo |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1.º (15:45) | 0 | 5 | 138 | 0 | 4 | 3 | 6 |
| 2.º, con las correcciones (17:00) | 0 | 3 | 140 | 0 | 4 | 0 | 6 |

Ninguna regla de inyección (SQL, comandos, plantillas, NoSQL, XSS reflejado o guardado) encontró algo: TS-02
**cumple**. Lo que se hizo con cada alerta:

| Alerta | Riesgo | Qué se hizo |
|---|---|---|
| Cookie No HttpOnly (`csrftoken`) | Bajo | Corregida: `CSRF_COOKIE_HTTPONLY = True` (ningún script lee la cookie) |
| Cross-Origin-Resource-Policy y Cross-Origin-Embedder-Policy | Bajo | Corregidas: Nginx las envía en todas las respuestas |
| Proxy Disclosure | Medio | Mitigada: Nginx solo acepta GET, HEAD y POST (TRACE y OPTIONS ya no llegan) y no muestra su versión. Sigue la cabecera `Server: nginx`, que no se puede quitar sin un módulo extra; se acepta porque no revela versión ni configuración |
| Bypassing 403 (`X-Original-URL`) | Medio | Falso positivo: con la cabecera la respuesta es la misma página de inicio, no un recurso prohibido. Además Nginx ya no pasa esa cabecera a la aplicación |
| CSP: `script-src` y `style-src` con `unsafe-inline` | Medio | Aceptada (D-25): algunas pantallas usan scripts y estilos en línea. El riesgo queda acotado porque toda entrada se muestra escapada (TS-02) y la política impide cargar recursos de otros sitios |
| Informativas (caché, sesión, «User Agent Fuzzer», atributo controlado por el usuario en el inicio de sesión) | Info | Sin acción: describen el comportamiento normal; el valor reflejado en el inicio de sesión se escapa |
