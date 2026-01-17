# Home-GPU-Cloud

**Sistema CaaS (Compute-as-a-Service) para alquiler de potencia GPU en una red local.**

Permite a usuarios enviar scripts de machine learning que se ejecutan en GPUs remotos con facturación por minuto.

## 🏗️ Arquitectura

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Nodo A        │     │   Nodo B        │     │   Nodo C        │
│   Controller    │     │   NAS/Storage   │     │   GPU Worker    │
│                 │     │                 │     │                 │
│ ▪ FastAPI       │────▶│ ▪ NFS Server    │◀────│ ▪ Celery Worker │
│ ▪ PostgreSQL    │     │ ▪ /mnt/data     │     │ ▪ Docker + GPU  │
│ ▪ Redis         │     │                 │     │ ▪ RTX 4090      │
│ ▪ Frontend      │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## ✨ Características

- 🎮 **GPU Access**: NVIDIA RTX 4090 con CUDA 12.1
- 💰 **Billing**: Facturación por minuto con kill-switch automático
- 📊 **Real-time Logs**: WebSocket streaming de logs en tiempo real
- 🔐 **Secure**: JWT auth, containers aislados, no-network mode
- 🎨 **Modern UI**: Frontend futurista con glassmorphism

## 🚀 Quick Start

### 1. Backend (Nodo A)

```bash
cd backend

# Configurar environment
cp ../.env.example .env
# Editar .env con tus credenciales

# Iniciar servicios
docker-compose up -d  # PostgreSQL + Redis

# Instalar dependencias
pip install -r requirements.txt

# Aplicar migraciones
alembic upgrade head

# Iniciar API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. NFS Storage (Nodo B)

```bash
sudo ./scripts/setup_nfs_server.sh
```

### 3. GPU Worker (Nodo C)

```bash
# Configurar NFS client
sudo ./scripts/setup_nfs_client.sh

# Build Docker image
cd docker
docker build -t home-gpu-cloud:standard -f Dockerfile.standard .

# Iniciar worker
cd ../worker
pip install -r requirements.txt
celery -A worker.celery_app worker -l info
```

### 4. Frontend

Simplemente abre `frontend/index.html` en tu navegador, o sírvelo con cualquier servidor HTTP:

```bash
cd frontend
python -m http.server 3000
```

## 📁 Estructura del Proyecto

```
home-gpu-cloud/
├── backend/                 # API FastAPI
│   ├── app/
│   │   ├── api/            # Endpoints REST
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── main.py
│   ├── alembic/            # Database migrations
│   ├── tests/              # Pytest tests
│   └── requirements.txt
├── frontend/               # Static HTML/CSS/JS
│   ├── css/               # Styles
│   ├── js/                # JavaScript
│   └── *.html             # Pages
├── worker/                 # Celery GPU worker
├── docker/                # Docker environment
├── shared/                # Shared utilities
└── scripts/               # Setup scripts
```

## 🧪 Testing

```bash
cd backend

# Run all tests
pytest -v

# With coverage
pytest --cov=app --cov-report=html

# Specific file
pytest tests/test_auth.py -v
```

## 🛠️ API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Crear cuenta |
| POST | `/api/v1/auth/login` | Login (JWT) |
| GET | `/api/v1/auth/me` | Perfil actual |
| GET | `/api/v1/jobs/` | Listar jobs |
| POST | `/api/v1/jobs/` | Crear job |
| GET | `/api/v1/jobs/{id}` | Detalle job |
| POST | `/api/v1/jobs/{id}/cancel` | Cancelar job |
| GET | `/api/v1/wallet/` | Ver wallet |
| POST | `/api/v1/wallet/topup` | Añadir créditos |
| WS | `/api/v1/ws/logs/{job_id}` | Logs en tiempo real |

## 🔧 Stack Tecnológico

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+ / FastAPI / Pydantic |
| Database | PostgreSQL 15 + Alembic |
| Queue | Redis + Celery |
| Container | Docker + NVIDIA Container Toolkit |
| Frontend | Vanilla HTML/CSS/JS |
| Storage | NFS v4 |

## 📄 Licencia

MIT License - uso libre para proyectos personales y comerciales.
