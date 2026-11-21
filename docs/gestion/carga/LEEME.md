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
