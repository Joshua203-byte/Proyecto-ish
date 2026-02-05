#!/bin/bash
# Script para crear un anuncio en Epochly Cloud

# Configuración
API_URL="http://localhost:8000/api/v1/ads/"

# Datos del anuncio (Puedes editarlos aquí)
TITLE="Mi Nuevo Anuncio"
IMAGE_URL="https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=2670&auto=format&fit=crop"
TARGET_URL="https://google.com"
DURATION=15

# Enviar petición POST
curl -X POST "$API_URL" \
     -H "Content-Type: application/json" \
     -d '{
           "title": "'"$TITLE"'",
           "image_url": "'"$IMAGE_URL"'",
           "target_url": "'"$TARGET_URL"'",
           "duration_seconds": '"$DURATION"',
           "is_active": true
         }'

echo -e "\n\n✅ Anuncio creado exitosamente."
