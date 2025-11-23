"""
Handlers: Interacción con Telegram (CAPA 1)
Handlers que interactúan directamente con la API de Telegram.
"""
from .menu_handlers import superadmin_main_menu, show_doctors_menu
from .doctor_handlers import (
    start_add_doctor,
    receive_doctor_name,
    receive_doctor_id,
    cancel_add_doctor,
    show_doctors_list,
    show_delete_menu,
    show_simple_restrict_menu,
    show_simple_permit_menu,
    simple_delete_doctor,
    simple_restrict_doctor,
    simple_permit_doctor,
    show_restrict_doctor,
    WAITING_FOR_DOCTOR_NAME,
    WAITING_FOR_DOCTOR_ID,
)
from .request_handlers import (
    show_requests_menu,
    show_request_detail,
    approve_request,
    reject_request,
)

__all__ = [
    'superadmin_main_menu',
    'show_doctors_menu',
    'start_add_doctor',
    'receive_doctor_name',
    'receive_doctor_id',
    'cancel_add_doctor',
    'show_doctors_list',
    'show_delete_menu',
    'show_simple_restrict_menu',
    'show_simple_permit_menu',
    'simple_delete_doctor',
    'simple_restrict_doctor',
    'simple_permit_doctor',
    'show_restrict_doctor',
    'WAITING_FOR_DOCTOR_NAME',
    'WAITING_FOR_DOCTOR_ID',
    'show_requests_menu',
    'show_request_detail',
    'approve_request',
    'reject_request',
]

