# 🚀 Guía de Inicio Rápido - HomeGPU Cloud (Modo Producción con Ngrok)

Esta guía explica cómo iniciar todo el sistema correctamente usando **PostgreSQL**, **Docker** y **Ngrok**, evitando problemas de `localhost`.

## 📋 Prerrequisitos
- **Docker Desktop** debe estar abierto y corriendo.
- **Python 3.11** instalado.
- **Ngrok** instalado.

---

## 1️⃣ Paso 1: Iniciar Base de Datos y Redis (Docker)
Abre una terminal (PowerShell) en la carpeta del proyecto y ejecuta:

```powershell
# Iniciar Redis, PostgreSQL y el Worker
docker-compose -f docker-compose.worker.yml up -d
```

✅ **Verificación:** Ejecuta `docker ps` y asegúrate de ver 3 contenedores:
1. `homegpu-worker`
2. `homegpu-postgres`
3. `homegpu-redis`

---

## 2️⃣ Paso 2: Iniciar Ngrok (Túnel Público)
Abre **otra** terminal y ejecuta:

```powershell
ngrok http 8000
```
Copia la **URL HTTPS** que te da Ngrok (ej. `https://uncontemned-terina-isoperimetrical.ngrok-free.dev`).

⚠️ **IMPORTANTE:** Si la URL de ngrok cambia, debes actualizarla en el archivo `.env` (líneas `BACKEND_URL` y `FRONTEND_URL` - **EXCEPTO** la que usa `host.docker.internal` al final del archivo).

---

## 3️⃣ Paso 3: Iniciar el Backend (+ Frontend)
Abre una **tercera** terminal en la carpeta `backend` y ejecuta:

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

El backend servirá automáticamente el frontend compilado.

---

## 4️⃣ Paso 4: ¡Usar la App!
⛔ **NO USES** `localhost:8000`.
✅ **USA** la URL de Ngrok: `https://...ngrok-free.dev`

1. Abre la URL de Ngrok en tu navegador.
2. Si es la primera vez, Ngrok mostrará una advertencia -> Click en **"Visit Site"**.
3. Inicia sesión y crea tus Jobs.

---

## 🛠️ Solución de Problemas Comunes

### 🔴 El Worker no procesa jobs (se queda en "Pending")
Si cambiaste de red o reiniciaste la PC, a veces Docker pierde conexión.
**Solución:** Reinicia el network de docker:
```powershell
docker-compose -f docker-compose.worker.yml down
docker-compose -f docker-compose.worker.yml up -d
```

### 🔴 Error "Network Error" en el Frontend
Es normal si usas Ngrok gratuito y dejas la página abierta mucho tiempo. Si el Job sigue corriendo (el tiempo avanza), **ignora el mensaje** o refresca la página.

### 🔴 Base de datos vacía / Error de Login
Si cambiaste de SQLite a PostgreSQL, la base de datos es nueva.
**Solución:** Regístrate nuevamente en la app.

### 🔴 Error de conexión a Redis en logs del Worker
Asegúrate de que en el archivo `.env` raíz, la variable sea:
`REDIS_URL=redis://host.docker.internal:6379/0`
(Esto permite que Docker vea el Redis en tu máquina Windows desde dentro del contenedor).
