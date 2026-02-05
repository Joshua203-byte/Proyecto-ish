# 🚀 Despliegue en Heroku (Frontend)

Esta guía te explica cómo subir tu frontend "frontend-react" a Heroku.

## Requisitos Previos
1.  Tener una cuenta en [Heroku](https://signup.heroku.com/).
2.  Tener instalada la [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli).
    ```bash
    curl https://cli-assets.heroku.com/install.sh | sh
    ```
3.  Haber hecho login: `heroku login`.

## Pasos para Desplegar

### 1. Crear la App en Heroku
Desde la terminal, estando en la raíz del proyecto (`/home/ish/Proyecto-ish`):

```bash
# Entra a la carpeta del frontend (Importante: Heroku detecta la app por el package.json)
# PERO como es un monorepo, hay estrategias. La más fácil es usar "git subtree".

# Primero, crea la app en Heroku
heroku create epochly-frontend
```

### 2. Configurar Buildpacks
Asegúrate de que Heroku sepa que es una app de Node.js:
```bash
heroku buildpacks:set heroku/nodejs -a epochly-frontend
```

### 3. Subir el código
Como tu frontend está en una subcarpeta (`frontend-react`), usaremos `git subtree` para subir SOLO esa carpeta a Heroku.

***IMPORTANTE:** Asegúrate de haber hecho commit de todos tus cambios antes de ejecutar esto.*

```bash
git add .
git commit -m "Preparando deploy a Heroku"
```

Ahora, empuja la subcarpeta:
```bash
git subtree push --prefix frontend-react heroku main
```

*(Si tarda un poco es normal, Heroku está instalando dependencias y construyendo el proyecto).*

### 4. Configurar Variables de Entorno (Opcional)
Si tu backend está en Ngrok, debes decirle a tu frontend dónde encontrarlo.
Pero recuerda: Tu frontend está construido con Vite. Las variables de entorno en Vite (`VITE_...`) se "queman" en el código en el momento del BUILD.
Variables como `PORT` las maneja Heroku automáticamente.

Si necesitas cambiar la URL del API, asegúrate de definirla **antes** de hacer el push, o configúrala en el dashboard de Heroku y vuelve a desplegar.

### 5. ¡Abrir!
```bash
heroku open -a epochly-frontend
```

---

## Cheat Sheet de Comandos

| Acción | Comando |
| :--- | :--- |
| **Login** | `heroku login` |
| **Ver Logs** | `heroku logs --tail -a epochly-frontend` |
| **Redesplegar** | `git subtree push --prefix frontend-react heroku main` |
