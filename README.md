# TechContent AI — Organización Inteligente de Contenido Técnico

**Hackathon ONE – Proyectos G9 | Alura + Oracle**

Solución para la organización inteligente de contenido técnico mediante técnicas de Ciencia de Datos, expuesta a través de una API REST en Java/Spring Boot con integración a OCI Object Storage.

---

## Tabla de Contenidos

- [Descripción](#descripción)
- [Arquitectura](#arquitectura)
- [Tecnologías](#tecnologías)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [CI/CD y Despliegue](#ci-y-despliegue)
- [API Endpoints](#api-endpoints)
- [Ejemplos de Uso](#ejemplos-de-uso)
- [Requisitos](#requisitos)
- [Instalación y Ejecución](#instalación-y-ejecución)
- [Equipo](#equipo)

---

## Descripción

**TechContent AI** permite organizar, clasificar y enriquecer contenido técnico de forma automática. Recibe textos técnicos (documentación, tutoriales, anotaciones de estudio, artículos) y utiliza modelos de Machine Learning para:

- **Clasificación temática** del contenido (Backend, Frontend, DevOps, Data Science, etc.)
- **Extracción de palabras clave** relevantes
- **Agrupación por temas similares** y **recomendación de contenidos relacionados**

El resultado se expone en formato JSON para su consumo por otras aplicaciones, plataformas educativas o equipos técnicos que deseen construir repositorios inteligentes de conocimiento.

---

## Arquitectura

```
                         ┌───────────────────────────────┐
                         │           VPS                  │
                         │                                │
  ┌──────────┐           │  ┌─────────────────┐          │       ┌──────────────┐
  │ Cliente  │──────────▶│  │  Spring Boot    │          │       │ OCI Object   │
  │ (REST)   │           │  │  (Java 17)      │──────────┼──────▶│ Storage      │
  └──────────┘           │  │  :8080          │          │◀──────│ (modelos,    │
                         │  └───────┬─────────┘          │       │  datasets)   │
                         │          │                     │       └──────────────┘
                         │          │ llamada HTTP interna │
                         │          ▼                     │
                         │  ┌─────────────────┐           │
                         │  │  Python ML API  │           │
                         │  │  (FastAPI)      │           │
                         │  │  :5000          │           │
                         │  └─────────────────┘           │
                         │                                │
                         └────────────────────────────────┘
```

### Componentes

| Componente | Tecnología | Descripción |
|---|---|---|
| **API Principal** | Java 17 + Spring Boot 3 | Recibe peticiones REST, valida entrada, orquesta el procesamiento y devuelve resultados JSON. |
| **Motor ML** | Python 3.11 + FastAPI | Servicio interno que carga el modelo serializado y ejecuta inferencia (clasificación, keywords, similitud). |
| **Notebook DS** | Jupyter / Google Colab | Exploración de datos (EDA), preprocesamiento de texto, entrenamiento y evaluación de modelos, serialización. |
| **VPS** | Linux (Ubuntu 22.04) | Servidor que aloja el backend Spring Boot y el microservicio Python ML. |
| **OCI Object Storage** | Bucket S3-compatible | Almacenamiento de modelos serializados (`.joblib`), datasets de entrenamiento y documentos procesados. |
| **Base de Datos** | PostgreSQL / H2 (desarrollo) | Persistencia opcional de resultados y metadatos de contenido procesado. |

### Flujo de Procesamiento

```
1. Cliente → POST /api/contenido  (JSON con título y texto)
2. Spring Boot valida la entrada
3. Spring Boot → POST http://localhost:5000/predict  (texto preprocesado)
4. FastAPI carga modelo desde Object Storage y ejecuta:
   - TF-IDF + vectorización del texto
   - Clasificación con Regresión Logística / Random Forest
   - Extracción de keywords con YAKE / TF-IDF scores
5. FastAPI → JSON con categoría, keywords, scores  →  Spring Boot
6. Spring Boot enriquece respuesta y la retorna al cliente
```

---

## Tecnologías

### Backend
- **Java 17** / **Spring Boot 3.2**
- **Spring Web** (REST API)
- **Spring Boot Actuator** (health checks, métricas)
- **Spring Validation** (validación de entrada)
- **Lombok** (reducción de boilerplate)
- **Maven** (gestión de dependencias y build)
- **JUnit 5 + Mockito** (pruebas)

### Ciencia de Datos
- **Python 3.11**
- **Pandas** — manipulación de datos
- **Scikit-learn** — TF-IDF, Regresión Logística, métricas
- **NLTK / spaCy** — procesamiento de lenguaje natural (tokenización, stopwords, lematización)
- **YAKE** — extracción de palabras clave
- **Joblib** — serialización del modelo

### Infraestructura
- **Oracle Cloud Infrastructure (OCI)**
- **Docker / Docker Compose** — containerización
- **Nginx** (opcional) — reverse proxy

---

## Estructura del Proyecto

```
hackaton-alura/
├── README.md
├── backend/                          # API REST en Java/Spring Boot
│   ├── pom.xml
│   ├── Dockerfile
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/techcontent/ai/
│   │   │   │   ├── TechContentAiApplication.java
│   │   │   │   ├── controller/
│   │   │   │   │   └── ContenidoController.java
│   │   │   │   ├── dto/
│   │   │   │   │   ├── ContenidoRequest.java
│   │   │   │   │   └── ContenidoResponse.java
│   │   │   │   ├── service/
│   │   │   │   │   ├── MlService.java
│   │   │   │   │   └── ContenidoService.java
│   │   │   │   ├── client/
│   │   │   │   │   └── PythonMlClient.java   # Cliente HTTP para FastAPI
│   │   │   │   ├── config/
│   │   │   │   │   ├── AppConfig.java
│   │   │   │   │   └── OciConfig.java
│   │   │   │   └── exception/
│   │   │   │       └── GlobalExceptionHandler.java
│   │   │   └── resources/
│   │   │       ├── application.yml
│   │   │       └── application-oci.yml
│   │   └── test/
│   │       └── java/com/techcontent/ai/
│   │           └── controller/
│   │               └── ContenidoControllerTest.java
│   └── .mvn/
│
├── ml-service/                       # Microservicio Python para inferencia
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py                   # FastAPI app entrypoint
│   │   ├── model_loader.py           # Carga del modelo desde OCI
│   │   ├── preprocessor.py           # Limpieza y vectorización de texto
│   │   ├── classifier.py             # Clasificación temática
│   │   ├── keywords.py               # Extracción de palabras clave
│   │   └── similarity.py             # Similitud entre documentos
│   └── models/                       # Modelos serializados (local/dev)
│       └── .gitkeep
│
├── notebooks/                        # Notebooks de Ciencia de Datos
│   ├── 01_eda_limpieza.ipynb         # Exploración y limpieza de datos
│   ├── 02_preprocesamiento.ipynb     # Tokenización, stopwords, TF-IDF
│   ├── 03_entrenamiento.ipynb        # Entrenamiento y evaluación
│   └── 04_serializacion.ipynb        # Serialización del modelo final
│
├── docker-compose.yml                # Orquestación backend + ML + DB (opcional)
├── .gitignore
└── .env.example
```

---

## CI/CD y Despliegue

### Integración OCI

El proyecto utiliza **OCI Object Storage** como servicio obligatorio de Oracle Cloud:

| Servicio | Uso |
|---|---|
| **OCI Object Storage** | Bucket para almacenar modelos serializados (`.joblib`), datasets de entrenamiento y documentos procesados. |

El resto de la infraestructura corre en **VPS (Linux)**.

### Pipeline CI/CD (GitHub Actions)

```
push → Run Tests (JUnit + Pytest) → Build Docker images →
  → Deploy to VPS via SSH
```

### Variables de Entorno OCI

```bash
OCI_CLI_USER=ocid1.user.oc1...
OCI_CLI_TENANCY=ocid1.tenancy.oc1...
OCI_CLI_REGION=sa-santiago-1
OCI_MODEL_BUCKET=techcontent-models
OCI_DATASET_BUCKET=techcontent-datasets
```

---

## API Endpoints

### `POST /api/contenido`

Clasifica un texto técnico y extrae palabras clave.

**Request Body:**
```json
{
  "titulo": "Introducción a Spring Boot",
  "texto": "En este contenido se presentan los conceptos básicos para la creación de APIs REST utilizando Java y Spring Boot. Se abordan temas como controladores, servicios, inyección de dependencias y configuración de proyectos."
}
```

**Response (200 OK):**
```json
{
  "id": "a1b2c3d4",
  "categoria": "Backend",
  "probabilidad": 0.89,
  "palabras_clave": ["Java", "Spring Boot", "API REST", "Inyección de dependencias"],
  "contenidos_relacionados": [
    {
      "id": "e5f6g7h8",
      "titulo": "Spring Boot Avanzado: Seguridad con JWT",
      "similitud": 0.76
    }
  ],
  "procesado_en": "2026-07-23T14:30:00Z"
}
```

### `POST /api/contenido/lote`

Procesa múltiples documentos en una sola petición.

**Request Body:**
```json
[
  {
    "titulo": "Guía de Docker",
    "texto": "Docker permite crear contenedores para aplicaciones..."
  },
  {
    "titulo": "Python para Data Science",
    "texto": "Pandas y NumPy son librerías fundamentales..."
  }
]
```

### `GET /api/contenido/buscar?q=spring+boot`

Búsqueda semántica por palabras clave entre contenidos previamente procesados.

### `GET /api/categorias`

Lista todas las categorías disponibles con la cantidad de documentos por categoría.

### `GET /actuator/health`

Health check del servicio.

---

## Ejemplos de Uso

### Ejemplo 1: Clasificación de contenido Backend
```bash
curl -X POST http://localhost:8080/api/contenido \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Introducción a Spring Boot",
    "texto": "Conceptos básicos para crear APIs REST con Java y Spring Boot."
  }'
```
**Respuesta:** Categoría `Backend` con probabilidad alta, keywords: Java, Spring Boot, API REST.

### Ejemplo 2: Clasificación de contenido Frontend
```bash
curl -X POST http://localhost:8080/api/contenido \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Fundamentos de React",
    "texto": "React es una librería de JavaScript para construir interfaces de usuario con componentes reutilizables y virtual DOM."
  }'
```
**Respuesta:** Categoría `Frontend`, keywords: React, JavaScript, Componentes, Virtual DOM.

### Ejemplo 3: Clasificación de contenido DevOps
```bash
curl -X POST http://localhost:8080/api/contenido \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "CI/CD con GitHub Actions",
    "texto": "Automatización de builds, tests y despliegues usando GitHub Actions y Docker para integración continua."
  }'
```
**Respuesta:** Categoría `DevOps`, keywords: CI/CD, GitHub Actions, Docker, Automatización.

---

## Requisitos

### Backend (Java)
- Java 17+
- Maven 3.8+
- Spring Boot 3.2

### ML Service (Python)
- Python 3.11+
- pip 23+
- FastAPI + Uvicorn

### Infraestructura
- Docker 24+ y Docker Compose v2
- VPS Linux (Ubuntu 22.04 recomendado)
- Cuenta OCI con acceso a Object Storage
- OCI CLI configurado (para acceso a buckets)

---

## Instalación y Ejecución

### 1. Clonar el repositorio
```bash
git clone git@github.com:No-Country-simulation/G9-LATAM-Team_40.git
cd G9-LATAM-Team_40
```

### 2. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con credenciales OCI y configuraciones
```

### 3. Ejecutar con Docker Compose
```bash
docker compose up -d
```
Esto levanta:
- Backend Spring Boot en `http://localhost:8080`
- ML Service Python en `http://localhost:5000`

### 4. Ejecutar sin Docker (desarrollo local)

**ML Service:**
```bash
cd ml-service
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

**Backend:**
```bash
cd backend
./mvnw spring-boot:run
```

### 5. Notebooks de Ciencia de Datos
```bash
cd notebooks
jupyter notebook
# Ejecutar en orden: 01 → 02 → 03 → 04
```

### 6. Probar la API
```bash
curl -X POST http://localhost:8080/api/contenido \
  -H "Content-Type: application/json" \
  -d '{"titulo":"Test","texto":"Spring Boot y Java para APIs REST"}'
```

---

## Equipo

**G9-LATAM-Team_40** — Hackathon ONE | Alura + Oracle

| Rol | Stack |
|---|---|
| Data Science | Python, Pandas, Scikit-learn, NLTK |
| Backend | Java 17, Spring Boot 3, Maven |
| Infraestructura / DevOps | OCI, Docker, CI/CD |
| Frontend (opcional) | React / HTML+CSS+JS |

---

## Licencia

Este proyecto es desarrollado para el Hackathon ONE – Proyectos G9 de Alura Latam + Oracle.
