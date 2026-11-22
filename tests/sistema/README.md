# Pruebas de sistema (TS-01 a TS-12)

Se agregan en P5 (apartado 4.5.2.4): Playwright para aceptación en Chrome, Edge y tableta, Locust para la
carga de 10 usuarios con más de 1,000 mascotas (`python manage.py cargar_datos_prueba --mascotas 1200 --historial 30`, D-22),
OWASP ZAP para seguridad y la prueba de restauración del respaldo (TS-07, `scripts/respaldo.py probar`).

| Caso | Dónde | Cómo se ejecuta |
|---|---|---|
| TS-01 | `test_TS01_acceso_directo.py` | CI (`pytest`) |
| TS-02 | `test_TS02_entradas_maliciosas.py` y ZAP (`docs/gestion/zap/`) | CI y en la laptop |
| TS-03 | `test_TS03_https_y_contrasenas.py` | CI |
| TS-04 | `tests/carga/ts04_navegadores.py` | En la laptop (Playwright) |
| TS-05 | `test_TS05_busquedas.py` y `tests/carga/ts05_busquedas.py` | CI y en la laptop |
| TS-06 | `tests/carga/locustfile.py` | En la laptop (Locust) |
| TS-07 | `scripts/respaldo.py ts07` | En la laptop con el servidor limpio |
| TS-08 | `scripts/monitor.py reporte` | En la laptop (tarea programada) |
| TS-09 | `test_TS09_privacidad_y_bitacora.py` | CI |
| TS-10 | `test_TS10_jornada_completa.py` (ensayo automático de TA-09) | CI |
| TS-11 | `test_TS11_contingencia.py` | CI |
| TS-12 | `test_TS12_descuento_simultaneo.py` | CI |
