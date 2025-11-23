"""
Vista: Presentación (CAPA 3)
Construcción de botones y templates de mensajes.
"""
from .keyboards import (
    get_doctors_management_keyboard,
    get_back_to_main_keyboard,
    get_back_to_doctors_keyboard,
    get_doctors_list_keyboard,
    get_delete_doctors_keyboard,
    get_restrict_doctors_keyboard,
    get_permit_doctors_keyboard,
    get_requests_list_keyboard,
    get_request_detail_keyboard,
)
from .messages import (
    format_doctor_added_success,
    format_doctor_add_error,
    format_doctor_list,
    format_doctor_delete_success,
    format_request_list,
    format_request_detail,
    format_request_approved,
    format_request_rejected,
    format_welcome_notification,
)

__all__ = [
    'get_doctors_management_keyboard',
    'get_back_to_main_keyboard',
    'get_back_to_doctors_keyboard',
    'get_doctors_list_keyboard',
    'get_delete_doctors_keyboard',
    'get_restrict_doctors_keyboard',
    'get_permit_doctors_keyboard',
    'get_requests_list_keyboard',
    'get_request_detail_keyboard',
    'format_doctor_added_success',
    'format_doctor_add_error',
    'format_doctor_list',
    'format_doctor_delete_success',
    'format_request_list',
    'format_request_detail',
    'format_request_approved',
    'format_request_rejected',
    'format_welcome_notification',
]

