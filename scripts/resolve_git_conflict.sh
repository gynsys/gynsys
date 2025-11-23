#!/bin/bash
# Script para resolver conflictos de git en PythonAnywhere

echo "🔍 Verificando cambios locales en wsgi.py..."
echo ""

# Ver qué cambios tienes
git diff wsgi.py

echo ""
echo "¿Qué quieres hacer?"
echo "1. Guardar tus cambios locales (stash) y actualizar"
echo "2. Descartar tus cambios locales y usar la versión del repo"
echo "3. Ver los cambios primero"
echo ""
read -p "Opción (1/2/3): " opcion

case $opcion in
  1)
    echo "💾 Guardando cambios locales..."
    git stash
    echo "📥 Actualizando desde GitHub..."
    git pull origin main
    echo "✅ Actualizado. Tus cambios están guardados en stash."
    echo "💡 Para recuperarlos: git stash pop"
    ;;
  2)
    echo "⚠️ Descartando cambios locales..."
    git checkout -- wsgi.py
    echo "📥 Actualizando desde GitHub..."
    git pull origin main
    echo "✅ Actualizado con la versión del repositorio."
    ;;
  3)
    echo "📄 Mostrando cambios:"
    git diff wsgi.py
    ;;
  *)
    echo "❌ Opción inválida"
    exit 1
    ;;
esac

