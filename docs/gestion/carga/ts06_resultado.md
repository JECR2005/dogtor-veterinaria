# TS-06 · 10 usuarios simultáneos (RNF-05)

Generado por `tests/carga/locustfile.py` (S5-14) contra el entorno con https (D-25). Criterio de la Tabla 4.15: 95 % de las operaciones en 2 s o menos y cero errores.

| Dato | Valor |
|---|---|
| Mascotas en la base | 1,200 |
| Usuarios | 10 (recepcionistas y veterinarios) |
| Operaciones | 14,626 |
| Errores | 0 |
| En 2 s o menos | 99.73 % |
| Percentil 95 | 200 ms |
| Mediana · máximo | 70 ms · 11,214 ms |
| Operaciones por segundo | 8.15 |
| Resultado | **Cumple** |

| Operación | Veces | Errores | Mediana (ms) | P95 (ms) | Máximo (ms) |
|---|---:|---:|---:|---:|---:|
| Buscar cliente (GET) | 1,381 | 0 | 42 | 130 | 10,890 |
| Consulta (GET) | 2,484 | 0 | 62 | 130 | 10,647 |
| Consultas del día (GET) | 849 | 0 | 37 | 77 | 4,984 |
| Generar ticket (POST) | 1,968 | 0 | 120 | 190 | 11,214 |
| Guardar consulta (POST) | 2,484 | 0 | 76 | 150 | 11,188 |
| Historial de la mascota (GET) | 843 | 0 | 36 | 80 | 5,370 |
| Inicio (GET) | 10 | 0 | 54 | 180 | 179 |
| Inicio de sesión (POST) | 10 | 0 | 510 | 1,100 | 1,065 |
| Inicio de sesión (formulario) (GET) | 10 | 0 | 27 | 37 | 37 |
| Lista de tickets (GET) | 652 | 0 | 180 | 320 | 11,148 |
| Registrar pago (POST) | 1,967 | 0 | 100 | 160 | 2,089 |
| Ticket nuevo (formulario) (GET) | 1,968 | 0 | 36 | 70 | 9,473 |
