## Requisitos que atiende

<!-- Ejemplo: RF-05, RD-02. Enlaza el issue: Cierra #__ -->
Cierra #

## Qué cambia

-

## Pruebas

| Caso (TU/TI/TA/TS) | Qué verifica | Resultado |
|---|---|---|
| | | |

## Lista de verificación del autor

- [ ] La rama sigue la convención `feature/<requisito>-<tema>` o `fix/def-<nnn>-<tema>`.
- [ ] Las reglas de negocio están en `services.py`, no en las vistas.
- [ ] Cada regla RD tocada tiene una prueba que intenta violarla.
- [ ] Si cambié la base: script en `bd/cambios/`, ajuste en `bd/01_tablas.sql`, modelo y migración, diccionario de datos (o decisión en `docs/decisiones.md`).
- [ ] No hay contraseñas, claves ni datos reales de clientes en el código ni en las pruebas.
- [ ] Si agregué una dependencia, actualicé `docs/componentes.md`.

## Lista de verificación del revisor

- [ ] El criterio de aceptación del requisito se cumple.
- [ ] Las vistas validan el permiso del rol (RNF-01).
- [ ] El código es legible y está en el componente correcto.
