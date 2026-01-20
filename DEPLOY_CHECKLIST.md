# 🚀 Home-GPU-Cloud: Deployment Checklist

Esta guía detalla los pasos exactos para llevar tu proyecto de "Simulación Local" a "Producción Real" cuando tengas tu hardware (Servidor GPU + NAS).

## 1. Hardware & OS Setup
- [ ] **Servidor Principal (Worker + Backend)**:
    - Instalar **Ubuntu Server 22.04 LTS** (Recomendado).
    - Asignar IP Estática (ej. `192.168.1.100`).
- [ ] **NAS (Almacenamiento)**:
    - Configurar carpetas compartidas vía NFS (Network File System).
    - Ruta exportada: `/volume1/homegpu_data`.

## 2. NVIDIA Drivers & Docker (Crucial)
Para que los contenedores "vean" la GPU:
```bash
# 1. Instalar Drivers de GPU
sudo apt install nvidia-driver-535 -y
nvidia-smi  # <- Verificar que se vea la GPU

# 2. Instalar Docker
curl -fsSL https://get.docker.com | sh

# 3. Instalar NVIDIA Container Toolkit
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

## 3. Montar el NAS
El worker necesita leer/escribir donde el NAS pueda guardar persistencia.
```bash
sudo apt install nfs-common
sudo mkdir -p /mnt/homegpu_data
# Añadir a /etc/fstab para montaje automático:
# 192.168.1.50:/volume1/homegpu_data  /mnt/homegpu_data  nfs  defaults  0  0
sudo mount -a
```

## 4. Configuración del Proyecto (Backend)
En el servidor:
1. Clonar el repositorio (o copiar los archivos).
2. Crear un archivo `.env` real (basado en `config.py`):
```ini
# Database (Usaremos Postgres en Docker)
DATABASE_URL=postgresql://homegpu:securepass@db:5432/homegpu
# Redis
REDIS_URL=redis://redis:6379/0
# Rutas
NFS_MOUNT_PATH=/mnt/homegpu_data
# Seguridad
SECRET_KEY=TU_CLAVE_SECRETA_LARGA
WORKER_SECRET=TU_CLAVE_WORKER_SECRETA
```

## 5. Base de Datos & Servicios
Usaremos un `docker-compose.prod.yml` (que debes crear) para levantar todo junto: Postgres, Redis y el Backend.

## 6. Worker Real (Adiós Simulación)
El código actual del Worker **automáticamente detectará** que Docker está disponible (`self.docker_manager` no fallará) y dejará de usar el modo simulación.
- Ejecutará `run_job` real.
- Lanzará contenedores reales usando la imagen `home-gpu-cloud:standard-v2`.

## 7. Internet & Dominio
- Configurar **Nginx** como Proxy Reverso (puerto 80/443 -> 8000).
- Usar **Cloudflare Tunnel** o abrir puertos en el router.
- Obtener certificado SSL (gratis con Let's Encrypt / Certbot).

---

### ✅ Resultado Final
Cuando completes esto:
1. El usuario sube `train.py`.
2. El Worker recibe la tarea.
3. El Worker lanza un contenedor Docker **con acceso a la GPU física**.
4. ¡El entrenamiento ocurre de verdad a velocidad luz! ⚡
