# 🚀 Despliegue en Vercel (Frontend)

Vercel es la mejor opción para aplicaciones React/Vite. Es gratis y no pide tarjeta de crédito para empezar.

## Opción Rápida: Desde la Terminal

No necesitas instalar nada globalmente. Usaremos `npx`.

### 1. Iniciar el Despliegue
Ejecuta el siguiente comando desde la carpeta del proyecto (`/home/ish/Proyecto-ish`):

```bash
npx vercel frontend-react
```

### 2. Responder las preguntas
La terminal te hará algunas preguntas. Aquí tienes las respuestas recomendadas:

| Pregunta | Respuesta |
| :--- | :--- |
| **Set up and deploy "~/Proyecto-ish/frontend-react"?** | `y` (Yes) |
| **Which scope do you want to deploy to?** | (Elige tu usuario, dale Enter) |
| **Link to existing project?** | `n` (No) |
| **What’s your project’s name?** | `epochly-frontend` (o dale Enter) |
| **In which directory is your code located?** | `./` (Dale Enter, ya estamos en la carpeta correcta gracias al comando) |
| **Want to modify these settings?** | `n` (No, Vercel detecta Vite automáticamente) |

### 3. ¡Listo!
Vercel construirá tu sitio y te dará una URL (ej. `https://epochly-frontend.vercel.app`).
Esa es tu URL de producción.

---

## Configuración de API (Importante)

Tu frontend en Vercel necesita saber dónde está tu Backend (tu PC con Ngrok).

1. Ve al panel de control de tu proyecto en Vercel (en el navegador).
2. Ve a **Settings** > **Environment Variables**.
3. Agrega una variable:
    - **Key**: `VITE_API_URL`
    - **Value**: `https://tu-url-de-ngrok.ngrok-free.app` (La URL que obtuviste antes)
4. Necesitarás "Redeployar" para que tome el cambio (o ejecuta `npx vercel --prod` de nuevo).

*Nota: Como tu backend está en tu casa (Ngrok), si apagas tu compu o cierras Ngrok, la web de Vercel dejará de poder contactar al backend.*
