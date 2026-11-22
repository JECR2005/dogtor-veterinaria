# TS-04 · Navegadores, tableta e impresión (S5-15, D-27)

## Automática (Playwright)

```powershell
pip install -r requirements-carga.txt
python -m playwright install chromium
python manage.py preparar_carga
python tests/carga/ts04_navegadores.py
```

Recorre en **Chrome**, **Edge** (los instalados en la laptop) y una **tableta de 10"** (Chromium con la
pantalla, el tacto y el agente de una Galaxy Tab S4 en horizontal) los flujos principales de RNF-07: buscar un
cliente, agendar, ver el calendario, imprimir la agenda, cobrar un ticket, guardar una consulta, emitir una
receta, ver el historial y la agenda de estética. Revisa que ninguna pantalla tenga desplazamiento horizontal y
que los PDF midan carta. Deja `ts04_resultado.md` aquí y capturas en `logs/ts04/`.

## Impresión (a mano, una vez)

Desde Chrome, con https://dogtor.local:

| # | Qué | Cómo | Esperado |
|---|---|---|---|
| 1 | Receta | En una consulta con receta, **PDF** → Imprimir (Ctrl + P) → «Guardar como PDF» o la impresora | Tamaño carta, una hoja, folio R-…, sin cortes |
| 2 | Ticket | En un ticket, **PDF para imprimir** → Imprimir | Tamaño carta, folio T-…, líneas, pagos y la leyenda «no es un comprobante fiscal» |
| 3 | Agenda (TS-11) | Agenda → **Imprimir agenda (contingencia)** → Imprimir | Carta horizontal, con alergias y casillas para anotar |
