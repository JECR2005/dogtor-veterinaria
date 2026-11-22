# Pruebas de rendimiento (TS-05 y TS-06, RNF-05)

Se ejecutan en la laptop contra el entorno con https (https://dogtor.local, D-25), con más de 1,000 mascotas:

```powershell
pip install -r requirements-carga.txt
python manage.py cargar_datos_prueba --mascotas 1200 --historial 30
python manage.py preparar_carga
python tests/carga/ts05_busquedas.py
locust -f tests/carga/locustfile.py --headless -u 10 -r 2 -t 30m --host https://dogtor.local --csv docs/gestion/carga/ts06 --html docs/gestion/carga/ts06.html
```

- `ts05_resultado.md`: tiempo de 11 búsquedas (clientes, mascotas, productos y tickets), 10 veces cada una.
- `ts06_resultado.md`: resumen de Locust (5 recepcionistas que cobran y 5 veterinarios que guardan consultas
  durante 30 minutos). `ts06_stats.csv` y el resto de los CSV se suben; `ts06.html` se queda en la laptop.

La integración continua también mide TS-05 en el servidor (`tests/sistema/test_TS05_busquedas.py`).
Los datos de la carga son ficticios y se quedan en la base; antes de la aceptación final (TA-09) la base se
vuelve a crear con `bd/ejecutar.py --recrear` y `cargar_datos_prueba` (D-26).

## Resultados (21/11/2026, JECR2005, laptop con Docker Desktop y SQL Server 2025)

| Prueba | Resultado | Detalle |
|---|---|---|
| TS-05 | **Cumple** | 1,200 mascotas; 11 búsquedas × 10 veces; la más lenta, 210 ms (mediana de 30 a 61 ms) |
| TS-06 | **Cumple** | 10 usuarios durante 30 min; 14,626 operaciones, 0 errores, 99.73 % en 2 s o menos (percentil 95: 200 ms; mediana: 70 ms) |

En TS-06 hubo dos pausas aisladas, en los minutos 20.6 y 21.8, en las que varias operaciones al mismo tiempo
tardaron de 5 a 11 s (0.27 % del total). Afectaron a todas las pantallas a la vez, incluso a las de solo
lectura, así que corresponden a una pausa del equipo (Docker Desktop/WSL o SQL Server en la misma laptop) y no a
un bloqueo entre operaciones. Ningún pago tardó más de 2.1 s y no hubo errores. Con el criterio de la Tabla
4.15 (95 % en 2 s o menos y cero errores) la prueba cumple con amplio margen. Se anota en riesgos (R14,
rendimiento) para vigilarlo en operación.

OBS-05 (navegación sin medición formal) y OBS-06 (tiempo de respuesta) de LV-03 quedan cerradas con estas dos
mediciones.
