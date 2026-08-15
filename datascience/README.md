# Sistema de Indexación y Grafo de Conocimiento RAG (GraphRAG)

Sistema integral en Python para el procesamiento, clasificación, estructuración en grafos de conocimiento y búsqueda avanzada mediante **GraphRAG de dos niveles**. El proyecto integra modelos de lenguaje (**Gemini** y **DeepSeek**) para la extracción, generación de taxonomías y síntesis de respuestas con contexto aumentado.

---

### Índice
1. [Descripción del Proyecto](#descripción-del-proyecto)
2. [Arquitectura y Flujo de Trabajo](#arquitectura-y-flujo-de-trabajo)
3. [Estructura del Repositorio](#estructura-del-repositorio)
4. [Detalle de Módulos y Funcionalidad](#detalle-de-módulos-y-funcionalidad)
5. [Instalación y Configuración](#instalación-y-configuración)
6. [Pruebas Automatizadas](#pruebas-automatizadas)

---

### Descripción del Proyecto

El objetivo principal de este sistema es transformar documentos extensos e inestructurados (como normativas, leyes o estándares ISO) en un **Grafo de Conocimiento** consultable. A través de un enfoque híbrido, el sistema no solo extrae texto, sino que descubre categorías, clasifica cada documento y permite realizar consultas en lenguaje natural mediante un motor **GraphRAG**.

---

### Arquitectura y Flujo de Trabajo

El flujo de procesamiento de la información se divide en 4 etapas principales:

```text
[ Documentos PDF / Texto ]
           │
           ▼
 [ 1. Extracción y Limpieza ]  ───> Normalización de texto y división en secciones (Markdown)
           │
           ▼
 [ 2. Descubrimiento ]          ───> LLM identifica categorías conceptuales (Etapa 1)
           │
           ▼
 [ 3. Clasificación ]           ───> Asignación masiva de taxonomías y metadatos (Etapa 2)
           │
           ▼
 [ 4. Grafo e Indexación ]      ───> Construcción del grafo de conocimiento y embeddings
           │
           ▼
 [ 5. Consulta GraphRAG ]       ───> Búsqueda en 2 niveles (Nodos + Secciones) + Respuesta LLM
```

1. **Extracción y Limpieza:** Parsea archivos fuente (PDF o texto) a un formato Markdown estructurado en secciones y limpia caracteres especiales o inconsistencias.

2. **Descubrimiento Taxonómico (Etapa 1):** Un modelo de lenguaje analizan fragmentos representativos para sugerir conceptualmente una lista de categorías emergentes.

3. **Clasificación en Producción (Etapa 2):** Se procesan todos los documentos asignándoles categorías de la taxonomía descubierta con sus respectivos niveles de confianza.

4. **Construcción del Grafo e Indexación:** Se relacionan los nodos (categorías y conceptos) con las secciones de texto. Se generan embeddings para la búsqueda vectorial.

5. **Retrieval & Generation (GraphRAG):**

* **Nivel 1:** La consulta del usuario recupera los $K$ nodos más cercanos en el grafo vectorial.

* **Nivel 2:** Se extraen las secciones de los documentos asociados a esos nodos y se realiza un re-ranking por similitud coseno.

* **Sintesis:** El LLM (DeepSeek) sintetiza la respuesta basándose únicamente en el contexto relevante delimitado.

---

### Estructura del Repositorio

```text
proyecto/
├── prompts/             # Prompts y plantillas estructuradas para los LLMs
├── scripts/             # Scripts ejecutables de automatización y procesamiento
│   ├── src/             # Código fuente principal de la aplicación
│   │   ├── api/         # Cliente LLM, rotación de modelos y fallback
│   │   ├── clasificacion/# Descubrimiento y asignación de taxonomías
│   │   ├── clean/       # Limpieza y normalización de textos
│   │   ├── extraccion/  # Procesamiento de documentos (PDF/Markdown) y fragmentación
│   │   ├── grafo/       # Construcción y exportación de grafos de conocimiento
│   │   ├── indexacion/  # Pipeline GraphRAG de 2 niveles y motor de búsqueda
│   │   ├── schemas/     # Modelos de datos Pydantic
│   │   ├── storage/     # Persistencia atómica, gestión de JSON y backups
│   │   ├── __init__.py
│   │   └── settings.py  # Configuración global y gestión de variables de entorno
├── tests/               # Suite de pruebas unitarias (pytest)
│   ├── __init__.py
│   ├── test_llm_rotation.py # Pruebas de fallback y redundancia de LLMs
│   ├── test_parsers.py      # Pruebas de fragmentación y parsing de Markdown
│   ├── test_schemas.py      # Validación de esquemas Pydantic
│   └── test_settings.py     # Carga de variables de entorno y rutas base
└── requirements.txt     # Dependencias del proyecto
```

---

###Detalle de Módulos y Funcionalidad

* **src/api/:** Contiene la abstracción para interactuar con las APIs de Gemini y DeepSeek. Implementa rotación automática de modelos y manejo de fallos para garantizar que la ejecución no se interrumpa por cuotas de API.

* **src/clean/** y **src/extraccion/:** Se encargan del preprocesamiento. Transforman documentos crudos en listas de secciones delimitadas con sus correspondientes títulos y bloques de texto.

* **src/clasificacion/:** Maneja el ciclo de vida de la taxonomía. Utiliza esquemas Pydantic para validar que las salidas del LLM coincidan exactamente con la estructura esperada.

* **src/grafo/** e **src/indexacion/:** Forman el núcleo del motor GraphRAG. Almacenan las relaciones nodo-documento y permiten realizar búsquedas semánticas eficientes en memoria mediante NumPy sin necesidad de infraestructura pesada.

* **src/storage/:** Garantiza la integridad de los datos. Toda escritura de resultados se hace primero en archivos temporales (.tmp) antes de reemplazarse atómicamente, y crea copias de respaldo fechadas (backup_YYYYMMDD_HHMMSS.json).

---

###Instalación y Configuración

1. **Clonar el repositorio e instalar dependencias**


#### Instalación y Configuración

1. Clonar el repositorio e instalar dependencias

```bash
git clone [https://github.com/No-Country-simulation/G9-LATAM-Team_40.git](https://github.com/No-Country-simulation/G9-LATAM-Team_40.git)

cd G9-LATAM-Team_40

pip install -r requirements.txt
```

2. **Configurar variables de entorno**

> Crea un archivo .env en la raíz del proyecto basándote en la configuración de src/settings.py:


```bash
GEMINI_API_KEY=tu_api_key_aqui
DEEPSEEK_API_KEY=tu_api_key_aqui
DEEPSEEK_BASE_URL=[https://api.deepseek.com](https://api.deepseek.com)
```

---

### Pruebas Automatizadas

El proyecto incluye pruebas unitarias para validar la configuración de entorno, parsers de Markdown, schemas de API y rotación de modelos LLM.

Para ejecutar la suite completa de pruebas:

```bash
pytest
```
