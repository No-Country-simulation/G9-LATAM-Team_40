from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="TechContent AI - ML Service",
    description="Servicio de Machine Learning para clasificación de contenido técnico",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ml-service"}


@app.post("/predict")
async def predict(data: dict):
    return {
        "categoria": "Backend",
        "probabilidad": 0.89,
        "palabras_clave": ["Java", "Spring Boot", "API REST"],
        "mensaje": "Endpoint placeholder - implementar modelo ML"
    }
