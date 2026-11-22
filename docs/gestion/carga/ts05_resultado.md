# TS-05 · Tiempo de búsqueda con más de 1,000 mascotas (RNF-05)

Generado por `python tests/carga/ts05_busquedas.py` (S5-13) contra el entorno con https (D-25). Criterio de la Tabla 4.15: 2 segundos o menos. Cada búsqueda se repite 10 veces; el tiempo incluye la página completa.

| Dato | Valor |
|---|---|
| Fecha | 2026-11-21 17:26 |
| Servidor | https://dogtor.local |
| Mascotas en la base | 1,200 |
| Búsqueda más lenta | 210 ms |
| Resultado | **Cumple** |

| Búsqueda | Pantalla | Mediana (ms) | Máximo (ms) | ≤ 2 s |
|---|---|---:|---:|:---:|
| Cliente por nombre | `/clientes/` | 43 | 100 | Sí |
| Cliente por apellido sin acento | `/clientes/` | 40 | 105 | Sí |
| Cliente por nombre y apellido | `/clientes/` | 39 | 102 | Sí |
| Cliente por teléfono | `/clientes/` | 48 | 102 | Sí |
| Cliente por nombre de mascota | `/clientes/` | 41 | 97 | Sí |
| Cliente sin coincidencias | `/clientes/` | 30 | 37 | Sí |
| Cliente para un ticket | `/ventas/nuevo/` | 44 | 210 | Sí |
| Producto por nombre | `/inventario/productos/` | 46 | 96 | Sí |
| Producto por código | `/inventario/productos/` | 45 | 87 | Sí |
| Productos con alerta | `/inventario/productos/` | 45 | 69 | Sí |
| Clientes dados de baja incluidos | `/clientes/` | 61 | 111 | Sí |
