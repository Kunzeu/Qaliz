#!/bin/bash

echo "🚀 Actualizando Qaliz desde Git..."

cd /home/ubuntu/QalizPy || exit 1

# Resetear cambios locales por si acaso
git reset --hard

# Traer lo último del repositorio
git pull origin main

# Reconstruir la imagen de Docker
docker build -t qaliz-bot .

# Detener y eliminar contenedor anterior
docker stop qaliz-bot-container
docker rm qaliz-bot-container

# Correr contenedor actualizado
docker run -d --restart always -p 8080:8080 --name qaliz-bot-container qaliz-bot

echo "✅ Bot actualizado y corriendo con la última versión del repo"
