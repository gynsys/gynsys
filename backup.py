#!/usr/bin/env python3
# backup.py
"""
Script independiente para realizar copias de seguridad de la base de datos SQLite.

Este script puede ejecutarse manualmente o programarse con cron para backups automáticos.
No tiene dependencias con el código del bot (como telegram-bot), por lo que puede ejecutarse
independientemente sin afectar el funcionamiento del bot.

Uso:
    python backup.py

El script:
1. Localiza la base de datos original (database/medical_bot.db)
2. Crea un directorio de backups si no existe (./backups/)
3. Crea una copia de seguridad con nombre: backup-medical_bot-YYYY-MM-DD_HHMMSS.db
4. Utiliza la API de backup online de SQLite3 para crear una copia consistente
5. Opcionalmente elimina backups antiguos (mantiene solo los últimos 7 días)
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from dotenv import load_dotenv
import os
import sqlite3
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Cargar variables de entorno
load_dotenv()

# Configuración
DB_PATH = "database/medical_bot.db"
BACKUP_DIR = "backups"
RETENTION_DAYS = 7  # Mantener backups de los últimos 7 días

# Configuración de Correo
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
BACKUP_EMAIL_RECIPIENT = os.getenv('BACKUP_EMAIL_RECIPIENT', '')


def create_backup_directory():
    """Crea el directorio de backups si no existe."""
    backup_path = Path(BACKUP_DIR)
    backup_path.mkdir(exist_ok=True)
    return backup_path


def generate_backup_filename() -> str:
    """
    Genera un nombre de archivo para la copia de seguridad con fecha y hora.
    
    Formato: backup-medical_bot-YYYY-MM-DD_HHMMSS.db
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    return f"backup-medical_bot-{timestamp}.db"


def send_backup_email(backup_file: Path) -> bool:
    """
    Envía el archivo de backup por correo electrónico.
    """
    if not SMTP_USER or not SMTP_PASSWORD or not BACKUP_EMAIL_RECIPIENT:
        print("Configuración de correo incompleta. No se enviará el email.")
        return False

    print(f"Enviando backup a {BACKUP_EMAIL_RECIPIENT}...")
    
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = BACKUP_EMAIL_RECIPIENT
    msg['Subject'] = f"Backup GynSys Bot - {backup_file.name}"
    
    body = f"""
    Respaldo automático de la base de datos del Bot.
    
    Archivo: {backup_file.name}
    Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
    Tamaño: {backup_file.stat().st_size / (1024*1024):.2f} MB
    """
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        with open(backup_file, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {backup_file.name}",
        )
        msg.attach(part)
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SMTP_USER, BACKUP_EMAIL_RECIPIENT, text)
        server.quit()
        print("Correo enviado exitosamente")
        return True
    except Exception as e:
        print(f"Error enviando correo: {e}")
        return False


def backup_database(source_db: str, backup_path: Path) -> bool:
    """
    Crea una copia de seguridad de la base de datos usando la API de backup online de SQLite3.
    
    Args:
        source_db: Ruta a la base de datos original
        backup_path: Directorio donde guardar el backup
        
    Returns:
        True si el backup fue exitoso, False en caso contrario
    """
    if not os.path.exists(source_db):
        print(f"Error: La base de datos no existe en {source_db}")
        return False
    
    backup_filename = generate_backup_filename()
    backup_file = backup_path / backup_filename
    
    try:
        # Conectar a la base de datos original
        source_conn = sqlite3.connect(source_db)
        
        # Crear conexión para el backup
        backup_conn = sqlite3.connect(str(backup_file))
        
        # Usar la API de backup online de SQLite3
        # Esto crea una copia consistente sin bloquear la base de datos original
        source_conn.backup(backup_conn)
        
        # Cerrar conexiones
        backup_conn.close()
        source_conn.close()
        
        # Verificar que el archivo se creó correctamente
        if backup_file.exists() and backup_file.stat().st_size > 0:
            file_size_mb = backup_file.stat().st_size / (1024 * 1024)
            print(f"Backup creado exitosamente: {backup_filename}")
            print(f"   Ubicación: {backup_file}")
            print(f"   Tamaño: {file_size_mb:.2f} MB")
            
            # Intentar enviar por correo (Deshabilitado temporalmente por petición del usuario)
            # send_backup_email(backup_file)
            
            return True
        else:
            print(f"Error: El archivo de backup se creó pero está vacío o no existe")
            return False
            
    except sqlite3.Error as e:
        print(f"Error de SQLite al crear el backup: {e}")
        return False
    except Exception as e:
        print(f"Error inesperado al crear el backup: {e}")
        return False


def cleanup_old_backups(backup_path: Path, retention_days: int):
    """
    Elimina backups antiguos, manteniendo solo los de los últimos 'retention_days' días.
    
    Args:
        backup_path: Directorio donde están los backups
        retention_days: Número de días a mantener
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted_count = 0
        
        for backup_file in backup_path.glob("backup-medical_bot-*.db"):
            # Extraer la fecha del nombre del archivo
            # Formato: backup-medical_bot-YYYY-MM-DD_HHMMSS.db
            try:
                filename_part = backup_file.stem.replace("backup-medical_bot-", "")
                file_date = datetime.strptime(filename_part, "%Y-%m-%d_%H%M%S")
                
                if file_date < cutoff_date:
                    backup_file.unlink()
                    deleted_count += 1
                    print(f"Eliminado backup antiguo: {backup_file.name}")
            except ValueError:
                # Si no se puede parsear la fecha, mantener el archivo
                print(f"No se pudo parsear la fecha de {backup_file.name}, se mantiene")
                continue
        
        if deleted_count > 0:
            print(f"Se eliminaron {deleted_count} backup(s) antiguo(s)")
        else:
            print(f"No hay backups antiguos para eliminar")
            
    except Exception as e:
        print(f"Error al limpiar backups antiguos: {e}")


def main():
    """Función principal del script de backup."""
    print("=" * 60)
    print("Iniciando proceso de backup de la base de datos")
    print("=" * 60)
    
    # Verificar que la base de datos existe
    if not os.path.exists(DB_PATH):
        print(f"Error: La base de datos no se encuentra en {DB_PATH}")
        print("   Verifica que la ruta sea correcta.")
        return 1
    
    # Crear directorio de backups
    backup_path = create_backup_directory()
    print(f"Directorio de backups: {backup_path.absolute()}")
    
    # Crear el backup
    print(f"\nCreando backup de {DB_PATH}...")
    success = backup_database(DB_PATH, backup_path)
    
    if not success:
        print("\nEl proceso de backup falló.")
        return 1
    
    # Limpiar backups antiguos
    print(f"\nLimpiando backups antiguos (manteniendo últimos {RETENTION_DAYS} días)...")
    cleanup_old_backups(backup_path, RETENTION_DAYS)
    
    print("\n" + "=" * 60)
    print("Proceso de backup completado exitosamente")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit(main())

