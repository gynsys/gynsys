"""
Módulo Admin: Gestión de SuperAdmin
Estructura organizada por capas:
- handlers/: Interacción con Telegram (CAPA 1)
- services/: Lógica + Datos fusionada (CAPA 2)
- views/: Presentación (CAPA 3)
- router.py: Despachador de callbacks (Semáforo)
- utils.py: Helpers genéricos
"""
from .router import handle_superadmin_callback
from .handlers.menu_handlers import superadmin_main_menu, show_doctors_menu
from .handlers.doctor_handlers import (
    start_add_doctor,
    receive_doctor_name,
    receive_doctor_id,
    cancel_add_doctor,
    show_doctors_list,
    show_restrict_doctor,
    WAITING_FOR_DOCTOR_NAME,
    WAITING_FOR_DOCTOR_ID,
)

# Mantener compatibilidad hacia atrás
# Exportar funciones principales que otros módulos pueden usar
__all__ = [
    'handle_superadmin_callback',
    'superadmin_main_menu',
    'start_add_doctor',
    'receive_doctor_name',
    'receive_doctor_id',
    'cancel_add_doctor',
    'show_doctors_menu',
    'show_doctors_list',
    'show_restrict_doctor',
    'WAITING_FOR_DOCTOR_NAME',
    'WAITING_FOR_DOCTOR_ID',
]

