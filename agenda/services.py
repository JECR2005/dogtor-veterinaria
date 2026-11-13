"""Servicios (reglas de negocio) del componente «Agenda y citas».

Aquí viven las reglas; las vistas solo las llaman. Así las pruebas de unidad las ejercitan sin pasar
por la interfaz (apartado 4.6.1). Se programan en P1:

- RF-05: agendar, reprogramar, cancelar con motivo y completar citas (P1).
- RD-02: rechazar citas fuera del horario laboral o empalmadas (P1).
- RD-04: asignar cada servicio solo al puesto compatible (P1).
"""
