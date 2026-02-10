"""
Sistema de métricas de salud para el bot de Telegram
Rastrea errores, mensajes enviados, uptime y estado general
"""

from datetime import datetime, timedelta
from typing import Dict, Any
import threading
import logging

logger = logging.getLogger(__name__)


class BotHealthMetrics:
    """
    Rastrea métricas de salud del bot
    Thread-safe para uso en aplicaciones multi-threaded
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self.start_time = datetime.now()
        self.total_messages_sent = 0
        self.total_messages_received = 0
        self.total_errors = 0
        self.errors_last_hour = 0
        self.last_error_time = None
        self.hourly_reset_time = datetime.now()
        
        # Contadores por tipo de error
        self.error_types = {
            'BadRequest': 0,
            'NetworkError': 0,
            'TimedOut': 0,
            'RemoteProtocolError': 0,
            'Other': 0
        }
    
    def log_message_sent(self):
        """Registra un mensaje enviado exitosamente"""
        with self._lock:
            self.total_messages_sent += 1
    
    def log_message_received(self):
        """Registra un mensaje recibido"""
        with self._lock:
            self.total_messages_received += 1
    
    def log_error(self, error_type: str = 'Other'):
        """Registra un error ocurrido"""
        with self._lock:
            self.total_errors += 1
            self.errors_last_hour += 1
            self.last_error_time = datetime.now()
            
            # Incrementar contador por tipo
            if error_type in self.error_types:
                self.error_types[error_type] += 1
            else:
                self.error_types['Other'] += 1
            
            # Resetear contador horario si pasó 1 hora
            self._reset_hourly_if_needed()
    
    def _reset_hourly_if_needed(self):
        """Resetea el contador horario si pasó 1 hora (debe llamarse con lock)"""
        now = datetime.now()
        if now - self.hourly_reset_time > timedelta(hours=1):
            self.errors_last_hour = 0
            self.hourly_reset_time = now
    
    def get_uptime_seconds(self) -> int:
        """Retorna el uptime en segundos"""
        return int((datetime.now() - self.start_time).total_seconds())
    
    def get_error_rate(self) -> float:
        """Retorna la tasa de error (errores / mensajes totales)"""
        with self._lock:
            total_operations = self.total_messages_sent + self.total_messages_received
            if total_operations == 0:
                return 0.0
            return self.total_errors / total_operations
    
    def get_health_status(self) -> str:
        """
        Retorna el estado de salud del bot
        - healthy: < 10 errores/hora y error rate < 1%
        - degraded: 10-50 errores/hora o error rate 1-5%
        - unhealthy: > 50 errores/hora o error rate > 5%
        """
        with self._lock:
            self._reset_hourly_if_needed()
            error_rate = self.get_error_rate()
            
            if self.errors_last_hour > 50 or error_rate > 0.05:
                return 'unhealthy'
            elif self.errors_last_hour > 10 or error_rate > 0.01:
                return 'degraded'
            else:
                return 'healthy'
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna todas las métricas en un diccionario"""
        with self._lock:
            self._reset_hourly_if_needed()
            
            uptime = self.get_uptime_seconds()
            uptime_str = str(timedelta(seconds=uptime))
            
            return {
                'status': self.get_health_status(),
                'uptime': uptime_str,
                'uptime_seconds': uptime,
                'total_messages_sent': self.total_messages_sent,
                'total_messages_received': self.total_messages_received,
                'total_errors': self.total_errors,
                'errors_last_hour': self.errors_last_hour,
                'error_rate': round(self.get_error_rate() * 100, 2),  # Porcentaje
                'error_rate_decimal': self.get_error_rate(),
                'last_error_time': self.last_error_time.isoformat() if self.last_error_time else None,
                'error_types': self.error_types.copy(),
                'start_time': self.start_time.isoformat()
            }
    
    def log_metrics(self):
        """Registra las métricas actuales en el log"""
        metrics = self.get_metrics()
        logger.info(
            f"📊 Bot Health - Status: {metrics['status'].upper()} | "
            f"Uptime: {metrics['uptime']} | "
            f"Messages: {metrics['total_messages_sent']}↑ {metrics['total_messages_received']}↓ | "
            f"Errors: {metrics['total_errors']} ({metrics['error_rate']}%) | "
            f"Last Hour: {metrics['errors_last_hour']} errors"
        )
    
    def reset(self):
        """Resetea todas las métricas (útil para testing)"""
        with self._lock:
            self.start_time = datetime.now()
            self.total_messages_sent = 0
            self.total_messages_received = 0
            self.total_errors = 0
            self.errors_last_hour = 0
            self.last_error_time = None
            self.hourly_reset_time = datetime.now()
            for key in self.error_types:
                self.error_types[key] = 0


# Instancia global de métricas (singleton)
_metrics_instance = None


def get_metrics() -> BotHealthMetrics:
    """Obtiene la instancia global de métricas (singleton)"""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = BotHealthMetrics()
    return _metrics_instance
