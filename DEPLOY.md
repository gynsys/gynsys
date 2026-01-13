# Guía de Despliegue en Digital Ocean

## ⚠️ IMPORTANTE: Tamaño del Proyecto
La carpeta `venv/` **NO debe subirse al servidor**.
*   **Motivo**: Contiene binarios específicos de Windows que no funcionan en Linux (Digital Ocean). Además, ocupa mucho espacio (~360MB).
*   **Solución**: El entorno virtual se recrea en el servidor automáticamente.

## Opción A: Despliegue con Git (Recomendado)
Esta es la forma más rápida y ligera.

1.  **En tu PC Local**:
    *   Asegúrate de que `venv/` esté en `.gitignore` (ya lo está).
    *   Guarda tus cambios:
        ```bash
        git add .
        git commit -m "Preparando despliegue"
        git push origin main
        ```

2.  **En Digital Ocean (Consola)**:
    *   Clona el repositorio:
        ```bash
        git clone https://github.com/tu-usuario/gynsys.git
        cd gynsys
        ```
    *   Ejecuta el script de despliegue:
        ```bash
        chmod +x deploy.sh
        ./deploy.sh
        ```

## Opción B: Subida Manual (SFTP / FileZilla)
Si prefieres subir los archivos manualmente:

1.  Sube **TODO** el contenido de la carpeta, **EXCEPTO**:
    *   ❌ `venv/` (Carpeta completa)
    *   ❌ `__pycache__/`
    *   ❌ `.git/` (si no usas git en el server)

2.  Una vez subido, en la consola del servidor:
    ```bash
    # Crear entorno virtual en Linux
    python3 -m venv venv
    
    # Ejecutar script de despliegue
    chmod +x deploy.sh
    ./deploy.sh
    ```

## Configuración Final
1.  Crea el archivo `.env` en el servidor con tus credenciales de producción:
    ```bash
    nano .env
    ```
    (Pega el contenido y ajusta `WEBHOOK=ON`).

2.  El bot se ejecutará en segundo plano usando `nohup` (según `deploy.sh`).
