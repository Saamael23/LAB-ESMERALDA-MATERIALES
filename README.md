# EMERALD LAB — Aplicación web

Aplicación Streamlit basada en el notebook `ESMERALDA_LAB_Berilio_Cromo.ipynb`.

## Ejecutar localmente

1. Instala Python 3.10 o superior.
2. Abre una terminal en esta carpeta.
3. Ejecuta:

```bash
pip install -r requirements.txt
streamlit run app.py
```

La aplicación se abrirá en el navegador, normalmente en `http://localhost:8501`.

## Publicar en internet con Streamlit Community Cloud

1. Crea una cuenta en GitHub y un repositorio nuevo.
2. Sube `app.py` y `requirements.txt` (el README es opcional).
3. Entra en https://share.streamlit.io/ e inicia sesión con GitHub.
4. Selecciona **Create app**, el repositorio, la rama y `app.py`.
5. Pulsa **Deploy**. Streamlit generará un enlace público para compartir.

## Contenido

- Laboratorio óptico: absorbancia, transmitancia y color estimado.
- Estructura cristalina 3D interactiva.
- Experimento conceptual de luz incidente y transmitida.
- Controles para concentración relativa de Cr³⁺ y espesor.
- Escenarios predefinidos.

## Alcance científico

El modelo conserva el planteamiento del notebook original: bandas gaussianas sintéticas,
escalamiento tipo Beer-Lambert y una estimación colorimétrica aproximada. La estructura
cristalina 3D es esquemática y amplifica visualmente los sitios de Cr para facilitar su
observación. No equivale a datos experimentales ni a una estructura refinada desde un CIF.
