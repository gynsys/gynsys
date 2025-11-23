import logging
import sys
from datetime import datetime
from config import LOGS_SYS

class BotLogger:
    def __init__(self, name):
        self.name = name
        self.setup_logger()
    
    def setup_logger(self):
        """Configura el sistema de logging"""
        self.logger = logging.getLogger(self.name)
        
        if LOGS_SYS:
            self.logger.setLevel(logging.INFO)
            
            # Formato del log
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # Handler para consola
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            # Handler para archivo
            file_handler = logging.FileHandler('bot.log', encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        else:
            # Si los logs están desactivados, usar NullHandler
            self.logger.addHandler(logging.NullHandler())
    
    def info(self, message):
        """Log nivel info"""
        self.logger.info(message)
    
    def error(self, message):
        """Log nivel error"""
        self.logger.error(message)
    
    def warning(self, message):
        """Log nivel warning"""
        self.logger.warning(message)
    
    def debug(self, message):
        """Log nivel debug"""
        self.logger.debug(message)

# Logger global para uso rápido
def get_logger(name):
    return BotLogger(name)

# Logger hardcodeado para uso permanente (siempre activo)
class PermanentLogger:
    def __init__(self, name):
        self.name = name
        self.setup_logger()
    
    def setup_logger(self):
        """Configura logger permanente (siempre activo)"""
        self.logger = logging.getLogger(f"permanent_{self.name}")
        self.logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Siempre loguear a archivo
        file_handler = logging.FileHandler('permanent_bot.log', encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def log_doctor_added(self, doctor_name, doctor_id, added_by):
        """Log específico para médicos agregados"""
        self.logger.info(f"MEDICO_AGREGADO - Nombre: {doctor_name}, ID: {doctor_id}, AgregadoPor: {added_by}")
    
    def log_user_action(self, user_id, action, details=""):
        """Log para acciones de usuario"""
        self.logger.info(f"USER_ACTION - UserID: {user_id}, Action: {action}, Details: {details}")

    def log_doctor_deleted(self, doctor_name, doctor_id, deleted_by):
        """Log específico para médicos eliminados"""
        self.logger.info(f"MEDICO_ELIMINADO - Nombre: {doctor_name}, ID: {doctor_id}, EliminadoPor: {deleted_by}")

    def log_doctor_restricted(self, doctor_name, doctor_id, restricted_by):
        """Log específico para médicos restringidos"""
        self.logger.info(f"MEDICO_RESTRINGIDO - Nombre: {doctor_name}, ID: {doctor_id}, RestringidoPor: {restricted_by}")    

# Instancia global de logger permanente
perm_logger = PermanentLogger("medical_bot")