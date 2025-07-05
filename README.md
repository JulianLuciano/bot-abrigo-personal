# Proyecto de Recomendación de Abrigo

Este proyecto consiste en un bot de Telegram que recomienda qué tipo de abrigo usar según la ubicación y el pronóstico del tiempo. El sistema se compone de dos partes principales: una API de predicción y un bot de Telegram que interactúa con los usuarios.

## Estructura del Proyecto

El repositorio está organizado en dos directorios principales:

-   `api/`: Contiene el código de la API RESTful que realiza las predicciones, el modelo de machine learning y el módulo para obtener datos del clima.
-   `bot/`: Contiene el código del bot de Telegram y sus funciones de utilidad.

---

## API de Predicción (`api/`)

La API es el cerebro del sistema. Se encarga de recibir una ubicación, obtener datos meteorológicos y utilizar un modelo de machine learning para predecir la recomendación de abrigo.

### Archivos Principales

-   **`api.py`**: Define el endpoint de la API y orquesta el proceso de predicción.
-   **`weather.py`**: Módulo para obtener datos meteorológicos de la API de Open-Meteo.
-   **`modelo_catboost3.cbm`**: Modelo de machine learning pre-entrenado (CatBoost).

### `api.py` - Funcionamiento Detallado

La API, construida con **FastAPI**, expone un único endpoint:

-   **`POST /predecir`**:
    -   **Entrada**: Un objeto JSON con `lat` (latitud), `lon` (longitud) y `lead` (horas hacia adelante).
    -   **Proceso**:
        1.  **Recepción y Logging**: Registra la petición recibida para facilitar el seguimiento.
        2.  **Cálculo de Tiempo**: Determina la fecha y hora exactas para la predicción, ajustando según el `lead` proporcionado.
        3.  **Llamada a `weather.py`**: Invoca a `obtener_data_clima` para obtener un DataFrame de Pandas con los datos meteorológicos correspondientes a la ubicación y hora.
        4.  **Preprocesamiento de Datos**:
            -   Calcula la probabilidad de precipitación combinando lluvia, nieve y chubascos.
            -   Elimina columnas que no son necesarias para el modelo.
            -   Crea la variable `season` (estación del año) a partir del mes, una característica importante para el modelo.
        5.  **Predicción**: Carga el modelo `modelo_catboost3.cbm` y utiliza el método `predict_proba` para obtener las probabilidades de cada tipo de abrigo.
        6.  **Construcción de la Respuesta**: Ensambla un diccionario con la primera y segunda recomendación más probable, sus probabilidades y datos climáticos clave (temperatura, humedad, sensación térmica, etc.).
    -   **Salida**: Devuelve el diccionario en formato JSON.

### `weather.py` - Módulo de Clima

Este módulo es el responsable de comunicarse con la API externa de **Open-Meteo**.

-   **`obtener_data_clima(base)`**:
    -   Recibe un DataFrame de Pandas (`base`) con la latitud, longitud y fecha.
    -   Construye una petición a la API de Open-Meteo solicitando una gran cantidad de variables meteorológicas horarias (temperatura, humedad, precipitación, viento, nubosidad, etc.).
    -   Utiliza `requests-cache` para cachear las respuestas de la API durante una hora, evitando peticiones repetidas y mejorando el rendimiento.
    -   Maneja la paginación de fechas y filtra los datos para obtener el pronóstico de la hora exacta requerida (`hour_integer`).
    -   Devuelve un DataFrame enriquecido con todas las variables climáticas, que luego es utilizado por `api.py`.

---

## Bot de Telegram (`bot/`)

El bot de Telegram, desarrollado con la librería **`python-telegram-bot`**, es la interfaz de usuario del sistema.

### Archivos Principales

-   **`bot.py`**: Contiene la lógica principal del bot, incluyendo los comandos y el manejo de la conversación.
-   **`utils.py`**: Funciones de utilidad para formatear los mensajes del bot.

### `bot.py` - Funcionamiento Detallado

-   **Manejo de Conversación (`ConversationHandler`)**: El bot utiliza un `ConversationHandler` para guiar al usuario a través de un flujo de preguntas y respuestas. Los estados de la conversación son:
    -   `ASK_HOURS`: Esperando que el usuario ingrese el número de horas.
    -   `ASK_COORDINATES`: Esperando las coordenadas o un atajo.
    -   `ASK_RAIN`: Esperando la respuesta del usuario sobre si quiere saber si lloverá.

-   **Comandos**:
    -   `/start`, `/help`: Comandos informativos.
    -   `/abrigo`, `/abrigo_2h`, `/abrigo_3h`, `/abrigo_4h`: Inician la conversación con un `lead` de 0, 2, 3 o 4 horas respectivamente.
    -   `/abrigo_nhs`: Inicia la conversación preguntando primero por el número de horas.

-   **`handle_coordinates(update, context)` - Lógica Clave**:
    1.  **Atajos de Ubicación**: Antes de procesar las coordenadas, la función verifica si el texto enviado por el usuario coincide con un atajo predefinido en el diccionario `location_shortcuts`. Por ejemplo, si el usuario escribe "caba", "casa" o "córdoba" (y sus variantes), el bot utiliza las coordenadas pre-asignadas para esas ubicaciones. Esto agiliza el uso para ubicaciones frecuentes.
    2.  **Validación de Coordenadas**: Si no es un atajo, la función valida que el texto tenga el formato `latitud,longitud`.
    3.  **Llamada a la API**: Envía las coordenadas y el `lead` a la API de predicción.
    4.  **Formateo del Mensaje**:
        -   Construye un mensaje claro y fácil de leer.
        -   Utiliza las funciones de `utils.py` (`temperatura_emoji`, `abrigo_emoji`) para añadir iconos visuales.
        -   **Lógica de Segunda Recomendación**: Muestra una segunda opción de abrigo si la probabilidad de la primera no es abrumadoramente alta (si `prob_1st` <= 60% o la diferencia con la segunda es pequeña), dando más flexibilidad al usuario.
    5.  **Botones Inline**: Muestra botones ("Sí" / "No") para preguntar al usuario si desea conocer la probabilidad de lluvia, haciendo la interacción más dinámica.

### `utils.py` - Funciones de Utilidad

Este módulo contiene funciones simples que ayudan a mejorar la experiencia del usuario:

-   **`temperatura_emoji(apparent_temperature)`**: Devuelve un emoji (`🥵`, `☀️`, `🥶`, etc.) según el rango de la sensación térmica.
-   **`abrigo_emoji(clase)`**: Devuelve un emoji (`👕`, `🧥`, `🧣`, etc.) correspondiente a la prenda recomendada.
-   **`lluvia_msj(prob, intensidad)`**: Devuelve un mensaje de texto sobre la necesidad de llevar paraguas, basado en la probabilidad e intensidad de la lluvia.

---

## Instalación y Despliegue

### API

1.  Navegá al directorio `api/`.
2.  Instalá las dependencias: `pip install -r requirements.txt`.
3.  Ejecutá la API con un servidor ASGI como Uvicorn: `uvicorn api:app --host 0.0.0.0 --port 8000`.

### Bot

1.  Navegá al directorio `bot/`.
2.  Instalá las dependencias: `pip install -r requirements.txt`.
3.  Configurá las variables de entorno:
    -   `TOKEN`: El token de tu bot de Telegram.
    -   `API_URL`: La URL donde está desplegada la API (ej: `http://localhost:8000/predecir`).
4.  Ejecutá el bot: `python bot.py`.
