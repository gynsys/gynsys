# Checklist de Seguridad del Servidor

Esta guía proporciona instrucciones prácticas para asegurar un servidor Linux (Ubuntu) donde se desplegará el bot médico de Telegram con base de datos SQLite.

## 📋 Tabla de Contenidos

1. [Acceso al Servidor](#1-acceso-al-servidor)
2. [Configuración del Firewall](#2-configuración-del-firewall)
3. [Mantenimiento del Sistema](#3-mantenimiento-del-sistema)
4. [Permisos de Archivos](#4-permisos-de-archivos)
5. [Configuración del Bot](#5-configuración-del-bot)
6. [Monitoreo y Logs](#6-monitoreo-y-logs)

---

## 1. Acceso al Servidor

### 1.1 Configuración de SSH con Clave

**Deshabilitar login por contraseña y usar solo claves SSH:**

```bash
# Editar configuración SSH
sudo nano /etc/ssh/sshd_config

# Asegurar estas líneas:
PasswordAuthentication no
PubkeyAuthentication yes
PermitRootLogin no
ChallengeResponseAuthentication no

# Reiniciar servicio SSH
sudo systemctl restart sshd
```

**Generar par de claves SSH (en tu máquina local):**

```bash
ssh-keygen -t ed25519 -C "tu_email@ejemplo.com"
ssh-copy-id usuario@tu_servidor
```

### 1.2 Deshabilitar Login del Usuario Root

```bash
# Ya configurado arriba con PermitRootLogin no
# Verificar que el usuario root no puede hacer login:
sudo passwd -l root
```

### 1.3 Cambiar Puerto SSH (Opcional pero Recomendado)

```bash
# Editar /etc/ssh/sshd_config
sudo nano /etc/ssh/sshd_config

# Cambiar:
Port 2222  # Usar un puerto diferente al 22

# Reiniciar SSH
sudo systemctl restart sshd

# IMPORTANTE: Antes de cerrar la sesión, probar la conexión en otra terminal
```

---

## 2. Configuración del Firewall

### 2.1 Instalar y Configurar UFW (Uncomplicated Firewall)

```bash
# Instalar UFW
sudo apt update
sudo apt install ufw -y

# Configurar reglas por defecto
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Permitir SSH (IMPORTANTE: hacer esto ANTES de activar el firewall)
sudo ufw allow 22/tcp
# O si cambiaste el puerto SSH:
sudo ufw allow 2222/tcp

# Permitir puerto HTTPS (si usas webhook)
sudo ufw allow 443/tcp

# Activar el firewall
sudo ufw enable

# Verificar estado
sudo ufw status verbose
```

### 2.2 Reglas Adicionales (si es necesario)

```bash
# Permitir HTTP (solo si es necesario)
sudo ufw allow 80/tcp

# Bloquear un IP específica
sudo ufw deny from 192.168.1.100

# Ver logs del firewall
sudo ufw logging on
sudo tail -f /var/log/ufw.log
```

---

## 3. Mantenimiento del Sistema

### 3.1 Actualizaciones del Sistema

```bash
# Actualizar lista de paquetes
sudo apt update

# Ver paquetes que pueden actualizarse
sudo apt list --upgradable

# Actualizar todos los paquetes
sudo apt upgrade -y

# Limpiar paquetes no utilizados
sudo apt autoremove -y
sudo apt autoclean
```

### 3.2 Actualizaciones de Seguridad Automáticas

**Instalar y configurar unattended-upgrades:**

```bash
# Instalar
sudo apt install unattended-upgrades -y

# Configurar
sudo dpkg-reconfigure -plow unattended-upgrades

# Verificar que está activo
sudo systemctl status unattended-upgrades
```

**Configuración manual (opcional):**

```bash
sudo nano /etc/apt/apt.conf.d/50unattended-upgrades

# Asegurar que estas líneas estén descomentadas:
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
```

### 3.3 Actualizaciones Programadas

```bash
# Crear script de actualización
sudo nano /usr/local/bin/system-update.sh

# Contenido del script:
#!/bin/bash
apt update && apt upgrade -y && apt autoremove -y

# Hacer ejecutable
sudo chmod +x /usr/local/bin/system-update.sh

# Programar con cron (ejecutar cada domingo a las 3 AM)
sudo crontab -e

# Añadir línea:
0 3 * * 0 /usr/local/bin/system-update.sh >> /var/log/system-update.log 2>&1
```

---

## 4. Permisos de Archivos

### 4.1 Permisos de la Base de Datos

```bash
# Restringir acceso a la base de datos
sudo chmod 600 database/medical_bot.db
sudo chown usuario:usuario database/medical_bot.db

# Verificar permisos
ls -l database/medical_bot.db
# Debe mostrar: -rw------- (solo lectura/escritura para el propietario)
```

### 4.2 Permisos del Archivo de Configuración

```bash
# Restringir acceso a config.py
sudo chmod 600 config.py
sudo chown usuario:usuario config.py

# Verificar permisos
ls -l config.py
# Debe mostrar: -rw------- (solo lectura/escritura para el propietario)
```

### 4.3 Permisos del Directorio del Proyecto

```bash
# Asegurar que el directorio del proyecto tenga permisos adecuados
sudo chmod 700 /ruta/al/proyecto
sudo chown -R usuario:usuario /ruta/al/proyecto

# Verificar
ls -ld /ruta/al/proyecto
# Debe mostrar: drwx------ (solo acceso para el propietario)
```

### 4.4 Permisos de Archivos de Logs

```bash
# Crear directorio de logs con permisos adecuados
mkdir -p logs
chmod 700 logs
chown usuario:usuario logs
```

---

## 5. Configuración del Bot

### 5.1 Variables de Entorno

**Crear archivo .env (NO commitear al repositorio):**

```bash
# Crear archivo .env
nano .env

# Contenido:
BOT_TOKEN=tu_token_aqui
ENCRYPTION_KEY=tu_clave_de_cifrado_aqui
SUPER_ADMIN_ID=tu_telegram_id

# Restringir permisos
chmod 600 .env
```

**Modificar config.py para leer de .env:**

```python
# Añadir al inicio de config.py
from dotenv import load_dotenv
load_dotenv()

# Luego usar:
BOT_TOKEN = os.getenv('BOT_TOKEN')
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
```

### 5.2 Ejecutar el Bot como Servicio

**Crear servicio systemd:**

```bash
sudo nano /etc/systemd/system/gynsys-bot.service
```

**Contenido del servicio:**

```ini
[Unit]
Description=GynSys Telegram Bot
After=network.target

[Service]
Type=simple
User=usuario
WorkingDirectory=/ruta/al/proyecto
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 /ruta/al/proyecto/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Activar y ejecutar el servicio:**

```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar para que inicie al arrancar
sudo systemctl enable gynsys-bot

# Iniciar el servicio
sudo systemctl start gynsys-bot

# Verificar estado
sudo systemctl status gynsys-bot

# Ver logs
sudo journalctl -u gynsys-bot -f
```

---

## 6. Monitoreo y Logs

### 6.1 Configurar Rotación de Logs

```bash
# Crear configuración de logrotate
sudo nano /etc/logrotate.d/gynsys-bot
```

**Contenido:**

```
/ruta/al/proyecto/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 usuario usuario
}
```

### 6.2 Monitoreo de Recursos

```bash
# Instalar herramientas de monitoreo
sudo apt install htop iotop nethogs -y

# Ver uso de CPU y memoria
htop

# Ver uso de disco
df -h

# Ver procesos del bot
ps aux | grep python
```

### 6.3 Alertas de Seguridad

**Instalar y configurar fail2ban (protección contra ataques de fuerza bruta):**

```bash
# Instalar
sudo apt install fail2ban -y

# Crear configuración local
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# Editar configuración
sudo nano /etc/fail2ban/jail.local

# Asegurar estas líneas:
[sshd]
enabled = true
port = 22
maxretry = 3
bantime = 3600

# Reiniciar fail2ban
sudo systemctl restart fail2ban
sudo systemctl enable fail2ban

# Verificar estado
sudo fail2ban-client status sshd
```

---

## 7. Backups Automáticos

### 7.1 Programar Backups con Cron

```bash
# Editar crontab
crontab -e

# Añadir línea para backup diario a las 2 AM
0 2 * * * /usr/bin/python3 /ruta/al/proyecto/backup.py >> /var/log/backup.log 2>&1
```

### 7.2 Verificar Backups

```bash
# Listar backups
ls -lh backups/

# Verificar integridad de un backup
sqlite3 backups/backup-medical_bot-YYYY-MM-DD_HHMMSS.db "PRAGMA integrity_check;"
```

---

## 8. Checklist Rápido

Antes de poner el servidor en producción, verifica:

- [ ] SSH configurado solo con claves (sin contraseñas)
- [ ] Usuario root deshabilitado para login
- [ ] Firewall (UFW) activado y configurado
- [ ] Sistema actualizado (`apt update && apt upgrade`)
- [ ] Actualizaciones automáticas configuradas
- [ ] Permisos de base de datos restringidos (600)
- [ ] Permisos de config.py restringidos (600)
- [ ] Variables sensibles en .env (no en config.py)
- [ ] Bot ejecutándose como servicio systemd
- [ ] Fail2ban configurado y activo
- [ ] Backups programados con cron
- [ ] Logs configurados con rotación

---

## 9. Recursos Adicionales

- [Documentación oficial de Ubuntu Security](https://ubuntu.com/security)
- [Guía de hardening de SSH](https://stribika.github.io/2015/01/04/secure-secure-shell.html)
- [Documentación de UFW](https://help.ubuntu.com/community/UFW)
- [Guía de systemd](https://www.freedesktop.org/software/systemd/man/systemd.service.html)

---

**Última actualización:** 2025-01-XX  
**Versión:** 1.0

