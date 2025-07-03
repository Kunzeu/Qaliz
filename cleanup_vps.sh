#!/bin/bash

echo "🧹 Iniciando limpieza del sistema..."

# 1. Limpiar Docker
docker system prune -af --volumes
echo "✅ Docker limpiado."

# 2. Borrar cache de pip
rm -rf ~/.cache/pip
echo "✅ Cache de pip eliminado."

# 3. Limpiar logs del sistema
journalctl --vacuum-time=3d
echo "✅ Logs antiguos purgados."

# 4. Eliminar archivos temporales típicos de editores (.swp y .tmp)
find ~ -type f \( -name "*.swp" -o -name "*.tmp" \) -delete
echo "✅ Archivos temporales borrados."

echo "✅ Limpieza completa, VPS listo para más batallas ⚔️"
