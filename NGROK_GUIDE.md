# 🌐 Guía de Despliegue con Ngrok

Esta guía explica cómo tu aplicación **Orion Cloud** ya está configurada para ser accesible públicamente usando Ngrok.

## 🚀 Arquitectura Actual

Tu configuración de `docker-compose` incluye un servicio de **Ngrok** dedicado que hace lo siguiente:
1.  Crea un túnel seguro desde internet hacia tu servicio **Frontend**.
2.  Tu Frontend (Nginx) sirve la página web React.
3.  Las peticiones al Backend (`/api/...`) son redirigidas por Nginx internamente hacia tu API (en el DGX).

**Resultado:** Solo necesitas UNA URL de ngrok para acceder a todo (Frontend y Backend).

## 🛠️ Pasos para Iniciar

### 1. Iniciar los servicios
Ejecuta el siguiente comando en la raíz del proyecto:
```bash
docker compose up -d
```
Esto levantará todos los contenedores: API, Base de Datos, Frontend y Ngrok.

### 2. Obtener tu URL Pública
Una vez que los servicios estén corriendo (espera unos 10 segundos), ejecuta:

```bash
docker compose logs ngrok
```

Busca una línea que diga algo parecido a:
`msg="started tunnel" obj=tunnels name=command_line addr=http://frontend:80 url=https://xxxx-xxxx.ngrok-free.app`

Tu URL es la que empieza con `https://...`.

### 3. ¡Listo!
Comparte esa URL. Al entrar, verás tu aplicación React, y podrá conectarse con el backend sin configuraciones extra.

---

## ⚠️ Solución de Problemas

**Si el túnel expira (free tier):**
Reinicia solo el servicio de ngrok para obtener una nueva URL:
```bash
docker compose restart ngrok
```

**Si no conecta:**
Verifica que todos los contenedores estén sanos:
```bash
docker compose ps
```
