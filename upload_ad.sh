#!/bin/bash
# Script INTELIGENTE para subir anuncios (Compatible con Canva/Archivos Locales)

BACKEND_URL="http://localhost:8000"

# 1. Pedir archivo
echo "📸 Arrastra aquí tu archivo de imagen (PNG/JPG) y pulsa Enter:"
read -r FILE_PATH
# Remove quotes/spaces if drag-and-drop adds them
FILE_PATH=$(echo "$FILE_PATH" | tr -d "'\"")

if [ ! -f "$FILE_PATH" ]; then
    echo "❌ El archivo no existe: $FILE_PATH"
    exit 1
fi

echo "📤 Subiendo imagen..."
UPLOAD_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/ads/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@$FILE_PATH")

# Extract URL using grep/sed (simple parsing)
IMAGE_URL=$(echo "$UPLOAD_RESPONSE" | grep -o '"url":"[^"]*' | cut -d'"' -f4)

if [ -z "$IMAGE_URL" ]; then
    echo "❌ Error subiendo imagen: $UPLOAD_RESPONSE"
    exit 1
fi

# Fix URL if it's relative
FULL_IMAGE_URL="$BACKEND_URL$IMAGE_URL"
echo "✅ Imagen subida: $FULL_IMAGE_URL"

# 2. Pedir datos restantes
echo -e "\n📝 Título del Anuncio:"
read -r TITLE

echo "🔗 Link de destino (ej: https://gotham.com/oferta):"
read -r TARGET_URL

echo "⏱️ Duración en segundos (Default: 15):"
read -r DURATION
DURATION=${DURATION:-15}

# 3. Crear Anuncio
echo -e "\n💾 Guardando anuncio..."
curl -s -X POST "$BACKEND_URL/api/v1/ads/" \
     -H "Content-Type: application/json" \
     -d '{
           "title": "'"$TITLE"'",
           "image_url": "'"$FULL_IMAGE_URL"'",
           "target_url": "'"$TARGET_URL"'",
           "duration_seconds": '"$DURATION"',
           "is_active": true
         }'

echo -e "\n\n🦇 ¡Listo! Tu anuncio de Canva ya está en rotación."
