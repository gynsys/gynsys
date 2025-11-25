# features/pdf_configuration/handlers.py
import logging
import tempfile
import os
import asyncio
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import (
    Application, CallbackQueryHandler, MessageHandler,
    ContextTypes, filters, ConversationHandler
)
from common.decorators import admin_required
from common.helpers import escape_html
from utils.role_manager import RoleManager
from config import DB_PATH

from . import states
from . import templates
from . import keyboards
from . import database as pdf_db

logger = logging.getLogger(__name__)

# Directorio base del proyecto y carpeta de logos
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOGOS_DIR = BASE_DIR / "logos"


def _resolve_logo_path(path_str: str) -> Path:
    """Convierte una ruta relativa (guardada en BD) a ruta absoluta."""
    if not path_str:
        return None
    path = Path(path_str)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path

# Helper para obtener doctor_id (multi-tenant)
role_manager = RoleManager(DB_PATH)

async def _get_doctor_id(update: Update) -> int:
    """Obtiene el doctor_id del usuario actual."""
    user_id = update.effective_user.id
    doctor = await role_manager.get_doctor_by_telegram_id(user_id)
    if doctor:
        return doctor[0]
    return None

# ===== HANDLERS PRINCIPALES =====

@admin_required
async def show_pdf_configuration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la configuración principal de PDF"""
    query = update.callback_query
    await query.answer()

    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await update.message.reply_text("❌ Error: No se pudo identificar tu perfil de médico.")
        return ConversationHandler.END
    
    settings = await pdf_db.get_pdf_settings(doctor_id)

    text = await templates.get_configuration_text(settings)
    keyboard = keyboards.get_configuration_keyboard(settings)

    await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode='HTML')

async def show_pdf_configuration_from_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la configuración principal desde un mensaje (no callback query)"""
    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await update.message.reply_text("❌ Error: No se pudo identificar tu perfil de médico.")
        return
    
    settings = await pdf_db.get_pdf_settings(doctor_id)

    text = await templates.get_configuration_text(settings)
    keyboard = keyboards.get_configuration_keyboard(settings)

    await update.message.reply_text(text=text, reply_markup=keyboard, parse_mode='HTML')

@admin_required
async def show_medical_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la sección de datos del médico"""
    query = update.callback_query
    await query.answer()

    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await update.message.reply_text("❌ Error: No se pudo identificar tu perfil de médico.")
        return ConversationHandler.END
    settings = await pdf_db.get_pdf_settings(doctor_id)

    text = "👨‍⚕️ <b>Configuración - Datos del Médico</b>\n\nEdita cada campo o controla su visibilidad en el PDF."
    keyboard = keyboards.get_medical_section_keyboard(settings)

    await query.edit_message_text(text=text, reply_markup=keyboard)

@admin_required
async def show_header_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la sección de encabezado y pie"""
    query = update.callback_query
    await query.answer()

    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await update.message.reply_text("❌ Error: No se pudo identificar tu perfil de médico.")
        return ConversationHandler.END
    settings = await pdf_db.get_pdf_settings(doctor_id)

    text = "📝 <b>Configuración - Encabezado y Pie</b>\n\nEdita cada campo o controla su visibilidad en el PDF."
    keyboard = keyboards.get_header_section_keyboard(settings)

    await query.edit_message_text(text=text, reply_markup=keyboard)

@admin_required
async def show_logos_section(update: Update, context: ContextTypes.DEFAULT_TYPE, message_to_edit_id: int = None):
    query = update.callback_query
    if query:
        await query.answer()

    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await update.message.reply_text("❌ Error: No se pudo identificar tu perfil de médico.")
        return ConversationHandler.END
    settings = await pdf_db.get_pdf_settings(doctor_id)

    text = "🖼️ <b>Configuración - Logos y Firmas</b>\n\nSube imágenes o controla su visibilidad en el PDF."
    keyboard = keyboards.get_logos_section_keyboard(settings)

    chat_id = update.effective_chat.id

    if message_to_edit_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_to_edit_id,
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        except BadRequest as e:
            logger.error(f"Error al editar para mostrar menú de logos: {e}")
    elif query and query.message:
        await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode='HTML')

# ===== FUNCIÓN AUXILIAR =====

async def show_logos_section_from_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la sección de logos desde un mensaje (no callback query)"""
    logger.info("🔄 Mostrando sección de logos desde mensaje...")

    try:
        doctor_id = await _get_doctor_id(update)
        if not doctor_id:
            logger.error("❌ No se pudo obtener doctor_id")
            if update.effective_message:
                await update.effective_message.reply_text("❌ Error: No se pudo identificar tu perfil de médico.")
            return

        settings = await pdf_db.get_pdf_settings(doctor_id)

        # Validar que settings no sea None
        if settings is None:
            logger.warning("⚠️ pdf_db.get_pdf_settings retornó None")
            settings = {}  # Usar diccionario vacío como fallback

        text = "🖼️ <b>Configuración - Logos y Firmas</b>\n\nSube imágenes o controla su visibilidad en el PDF."
        keyboard = keyboards.get_logos_section_keyboard(settings)

        # Usar effective_message que es más robusto
        if update.effective_message:
            await update.effective_message.reply_text(text=text, reply_markup=keyboard, parse_mode='HTML')
        else:
            # Fallback: enviar mensaje directamente
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )

        logger.info("✅ Sección de logos mostrada")

    except Exception as e:
        logger.error(f"❌ Error crítico en show_logos_section_from_message: {e}", exc_info=True)
        # Intentar enviar mensaje de error
        try:
            error_text = "❌ Ocurrió un error al cargar la configuración de logos."
            if update.effective_message:
                await update.effective_message.reply_text(error_text)
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=error_text
                )
        except Exception as final_error:
            logger.error(f"❌ Error incluso al enviar mensaje de error: {final_error}")
# ===== HANDLERS DE EDICIÓN DE TEXTO =====

@admin_required
async def start_edit_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia la edición de un campo de texto"""
    query = update.callback_query
    await query.answer()

    # El formato del callback es: pdf_edit_text:field_key
    field_key = query.data.split(':')[1]
    context.user_data['editing_field'] = field_key

    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await update.message.reply_text("❌ Error: No se pudo identificar tu perfil de médico.")
        return ConversationHandler.END
    current_value = await pdf_db.get_setting_value(doctor_id, field_key)

    # Nombres amigables para los campos
    field_names = {
        'doctor_name': 'Nombre del Médico',
        'specialty': 'Especialidad',
        'location': 'Ubicación',
        'phones': 'Teléfonos',
        'mpps_number': 'Número MPPS',
        'cmdm_number': 'Número CMDM',
        'doctor_id': 'Cédula del Médico',
        'report_title': 'Título del Informe',
        'footer_city': 'Ciudad del Pie de Página'
    }

    field_name = field_names.get(field_key, field_key)
    text = templates.get_edit_field_text(field_name, current_value)
    keyboard = keyboards.get_cancel_keyboard()
    
    await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode='HTML')
    return states.AWAITING_TEXT_INPUT

async def process_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa el nuevo valor para un campo de texto"""
    new_value = update.message.text
    field_key = context.user_data.get('editing_field')

    if new_value.lower() == 'cancelar':
        await update.message.reply_text("❌ Edición cancelada.")
        await show_pdf_configuration_from_message(update, context)
        return ConversationHandler.END

    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await update.message.reply_text("❌ Error: No se pudo identificar tu perfil de médico.")
        return ConversationHandler.END
    success = await pdf_db.update_pdf_setting(doctor_id, field_key, new_value)

    if success:
        await update.message.reply_text("✅ Campo actualizado correctamente.")
    else:
        await update.message.reply_text("❌ Error al actualizar el campo.")

    await show_pdf_configuration_from_message(update, context)
    return ConversationHandler.END

# ===== HANDLERS DE VISIBILIDAD =====

@admin_required
async def toggle_visibility(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Alterna la visibilidad de un campo"""
    query = update.callback_query
    await query.answer()

    field_key = query.data.split(':')[1]
    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await query.edit_message_text("❌ Error: No se pudo identificar tu perfil de médico.")
        return

    success = await pdf_db.toggle_setting_visibility(doctor_id, field_key)

    if success:
        # Determinar de qué sección venimos para redirigir correctamente
        if field_key.startswith('logo_'):
            await show_logos_section(update, context)
        elif field_key in ['report_title', 'footer_city']:
            await show_header_section(update, context)
        else:
            await show_medical_section(update, context)
    else:
        await query.answer("❌ Error al cambiar visibilidad", show_alert=True)

@admin_required
async def toggle_functional_exam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Alterna la inclusión del examen funcional en la preconsulta"""
    query = update.callback_query
    await query.answer()

    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await query.edit_message_text("❌ Error: No se pudo identificar tu perfil de médico.")
        return

    # Obtener el valor actual
    settings = await pdf_db.get_pdf_settings(doctor_id)
    current_value = settings.get('include_functional_exam', {}).get('value', '1')
    
    # Alternar: '1' -> '0', '0' -> '1'
    new_value = '0' if current_value == '1' else '1'
    
    # Actualizar en la base de datos
    success = await pdf_db.update_pdf_setting(doctor_id, 'include_functional_exam', new_value, is_visible=True)
    
    if success:
        status_text = "incluido" if new_value == '1' else "excluido"
        await query.answer(f"✅ Examen Funcional {status_text} de la preconsulta", show_alert=True)
        # Refrescar el menú principal
        await show_pdf_configuration(update, context)
    else:
        await query.answer("❌ Error al cambiar configuración", show_alert=True)

# ===== HANDLERS PARA SUBIDA DE LOGOS =====
@admin_required
async def start_logo_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Inicia el proceso de subida de un logo, EDITANDO el mensaje actual
    y guardando su ID para futuras ediciones.
    """
    query = update.callback_query
    await query.answer()

    logo_key = query.data.split(':')[1]
    context.user_data['uploading_logo_type'] = logo_key

    # --- INICIO DE LA CORRECCIÓN CLAVE ---
    # Guardamos el ID del mensaje que vamos a estar editando
    context.user_data['logo_editor_message_id'] = query.message.message_id
    # --- FIN DE LA CORRECCIÓN CLAVE ---

    logo_names = {
        'logo_header_1': 'Logo Superior Izquierdo',
        'logo_header_2': 'Logo Superior Derecho',
        'logo_signature': 'Firma y Sello'
    }
    logo_name = logo_names.get(logo_key, 'Logo')

    text = f"📤 <b>Subiendo: {logo_name}</b>\n\nEnvía la imagen o escribe 'cancelar' para abortar."

    await query.edit_message_text(text=text, reply_markup=keyboards.get_cancel_keyboard(), parse_mode='HTML')

    return states.AWAITING_LOGO_UPLOAD


@admin_required
async def process_logo_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("--- [LOGO UPLOAD] Iniciando process_logo_upload ---")
    message = update.effective_message
    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        if message:
            await message.reply_text("❌ Error: No se pudo identificar tu perfil de médico.")
        return ConversationHandler.END

    logo_key = context.user_data.get('uploading_logo_type')
    editor_message_id = context.user_data.get('logo_editor_message_id')

    if not all([editor_message_id, message, logo_key]):
        logger.warning("[LOGO UPLOAD] Faltan datos críticos. Abortando.")
        return ConversationHandler.END

    file_to_download = None
    file_extension = '.jpg'

    if message.photo:
        logger.info("[LOGO UPLOAD] Imagen recibida como foto")
        photo = message.photo[-1]
        file_to_download = await photo.get_file()
        file_extension = os.path.splitext(file_to_download.file_path)[1] or '.jpg'
    elif message.document and message.document.mime_type.startswith('image/'):
        logger.info("[LOGO UPLOAD] Imagen recibida como documento")
        file_to_download = await message.document.get_file()
        file_name = message.document.file_name or file_to_download.file_path
        file_extension = os.path.splitext(file_name)[1] or '.jpg'
    else:
        logger.warning("[LOGO UPLOAD] Archivo no válido")
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=editor_message_id,
            text="❌ Debes enviar una imagen válida."
        )
        return ConversationHandler.END

    try:
        LOGOS_DIR.mkdir(parents=True, exist_ok=True)
        new_filename = f"logo_{doctor_id}_{logo_key}{file_extension}"
        file_path = LOGOS_DIR / new_filename
        await file_to_download.download_to_drive(str(file_path))

        relative_path = file_path.relative_to(BASE_DIR).as_posix()
        success = await pdf_db.update_pdf_setting(doctor_id, logo_key, relative_path)

        if success:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=editor_message_id,
                text="✅ Logo actualizado con éxito."
            )
        else:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=editor_message_id,
                text="❌ Error al guardar en la base de datos."
            )

    except Exception as e:
        logger.error(f"[LOGO UPLOAD] Excepción: {e}", exc_info=True)
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=editor_message_id,
            text="❌ Error inesperado."
        )

    await asyncio.sleep(2)
    await show_logos_section(update, context, message_to_edit_id=editor_message_id)

    if message:
        await message.delete()

    context.user_data.clear()
    return ConversationHandler.END

@admin_required
async def confirm_logo_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra confirmación para eliminar un logo"""
    query = update.callback_query
    await query.answer()

    # El formato del callback es: pdf_delete_logo:logo_key
    logo_key = query.data.split(':')[1]
    context.user_data['deleting_logo_type'] = logo_key

    text = templates.get_delete_confirmation_text(logo_key)
    keyboard = keyboards.get_confirm_delete_keyboard(logo_key)

    await query.edit_message_text(text=text, reply_markup=keyboard)
    return states.CONFIRMING_DELETE

@admin_required
async def execute_logo_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ejecuta la eliminación del logo"""
    query = update.callback_query
    await query.answer()

    logo_key = context.user_data.get('deleting_logo_type')
    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await query.edit_message_text("❌ Error: No se pudo identificar tu perfil de médico.")
        return

    if logo_key:
        # Obtener la ruta actual para eliminar el archivo
        current_value = await pdf_db.get_setting_value(doctor_id, logo_key)

        # Eliminar el archivo físico si existe
        resolved_current = _resolve_logo_path(current_value)
        if resolved_current and resolved_current.exists():
            try:
                resolved_current.unlink()
                logger.info(f"Archivo de logo eliminado: {resolved_current}")
            except Exception as e:
                logger.error(f"Error eliminando archivo de logo: {e}")

        # Actualizar la base de datos
        success = await pdf_db.update_pdf_setting(doctor_id, logo_key, None)

        if success:
            await query.answer("✅ Logo eliminado correctamente.", show_alert=True)
        else:
            await query.answer("❌ Error al eliminar el logo.", show_alert=True)

        # Limpiar user_data
        context.user_data.pop('deleting_logo_type', None)

    # Volver a la sección de logos
    await show_logos_section(update, context)
    return ConversationHandler.END

# ===== HANDLERS DE CANCELACIÓN =====

async def cancel_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela la operación actual y vuelve al menú principal"""
    query = update.callback_query
    await query.answer()

    await show_pdf_configuration(update, context)
    return ConversationHandler.END

async def cancel_operation_from_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela la operación actual desde un mensaje de texto"""
    await update.message.reply_text("❌ Operación cancelada.")
    await show_pdf_configuration_from_message(update, context)
    return ConversationHandler.END

async def invalid_input_in_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Informa al usuario sobre una entrada inválida durante la subida de logo."""
    editor_message_id = context.user_data.get('logo_editor_message_id')
    if update.message:
        await update.message.delete()
    if editor_message_id:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id, message_id=editor_message_id,
            text="❌ **Entrada no válida.**\n\nPor favor, envía una imagen o escribe 'cancelar'.",
            reply_markup=keyboards.get_cancel_keyboard(), parse_mode='HTML'
        )
    return states.AWAITING_LOGO_UPLOAD

async def invalid_input_in_text_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Informa al usuario que ha enviado un tipo de mensaje incorrecto durante la edición de texto."""
    await update.message.reply_text(
        "❌ **Entrada no válida.**\n\nPor favor, envía solo texto o escribe 'cancelar' para abortar."
    )
    # Mantenemos al usuario en el mismo estado
    return states.AWAITING_TEXT_INPUT
# ===== REGISTRO DE HANDLERS =====

def register(app: Application):
    """Registra todos los handlers del módulo de forma robusta."""

    # ---------- 1) CONVERSATION HANDLERS (SIEMPRE PRIMERO) ----------

    # Conversación para edición de texto (CORREGIDA)
    text_edit_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_edit_text, pattern='^pdf_edit_text:')],
    states={
        states.AWAITING_TEXT_INPUT: [
            MessageHandler(filters.TEXT & filters.Regex('^(cancelar|Cancelar)$'), cancel_operation_from_message),
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_text_input),
            MessageHandler(~filters.TEXT & ~filters.COMMAND, invalid_input_in_text_edit),
        ]
    },
    fallbacks=[
        CallbackQueryHandler(cancel_operation, pattern='^pdf_config_cancel$')
    ],
    # --- CAMBIOS CLAVE AQUÍ ---
    name="pdf_text_edit_conversation", # Nombre único para la conversación
    persistent=False, # Si usas persistencia, configúrala globalmente en ApplicationBuilder
    allow_reentry=True # Buena práctica
    # Eliminamos per_message, per_chat y per_user, PTB usará su comportamiento por defecto que es per_user y per_chat
)

    # Conversación: Subida de logos (CORREGIDA)
    logo_upload_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_logo_upload, pattern='^pdf_upload_logo:')],
    states={
        states.AWAITING_LOGO_UPLOAD: [
            MessageHandler(filters.PHOTO | filters.Document.IMAGE, process_logo_upload),
            MessageHandler(filters.TEXT & filters.Regex('^(cancelar|Cancelar)$'), cancel_operation_from_message),
            MessageHandler(filters.ALL & ~filters.COMMAND, invalid_input_in_upload)
        ]
    },
    fallbacks=[
        CallbackQueryHandler(cancel_operation, pattern='^pdf_config_cancel$')
    ],
    # --- APLICAMOS LA MISMA SIMPLIFICACIÓN AQUÍ ---
    name="pdf_logo_upload_conversation",  # Nombre único para la conversación
    persistent=False,
    allow_reentry=True
    # Eliminamos per_message, per_chat y per_user
)
    # Conversación: Eliminación de logos (Ligeramente simplificada)
    logo_delete_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(confirm_logo_delete, pattern='^pdf_delete_logo:')],
        states={
            states.CONFIRMING_DELETE: [
                # El usuario solo puede interactuar con botones en este estado
                CallbackQueryHandler(execute_logo_delete, pattern='^pdf_delete_confirm:'),
                # El botón de cancelar general también funciona aquí
                CallbackQueryHandler(cancel_operation, pattern='^pdf_config_cancel$')
            ]
        },
        fallbacks=[
            # Un fallback general por si la conversación se interrumpe
            CallbackQueryHandler(cancel_operation, pattern='^pdf_config_cancel$')
        ],
        per_message=True,
        per_chat=True,
        per_user=True
    )

    # Registrar ConversationHandlers
    app.add_handler(text_edit_conv)
    app.add_handler(logo_upload_conv)
    app.add_handler(logo_delete_conv)

    # ---------- 2) HANDLERS BÁSICOS DE NAVEGACIÓN (SIN ESTADOS) ----------
    app.add_handler(CallbackQueryHandler(show_pdf_configuration, pattern='^pdf_configuration_menu$'))
    app.add_handler(CallbackQueryHandler(show_pdf_configuration, pattern='^pdf_config_main$'))
    app.add_handler(CallbackQueryHandler(show_medical_section, pattern='^pdf_config_medical_section$'))
    app.add_handler(CallbackQueryHandler(show_header_section, pattern='^pdf_config_header_section$'))
    app.add_handler(CallbackQueryHandler(show_logos_section, pattern='^pdf_config_logos_section$'))
    app.add_handler(CallbackQueryHandler(toggle_visibility, pattern='^pdf_toggle_visibility:'))
    app.add_handler(CallbackQueryHandler(toggle_functional_exam, pattern='^pdf_toggle_functional_exam$'))
    # No es necesario registrar cancel_operation aquí de nuevo, ya está en los fallbacks.
    # Pero no hace daño tenerlo por si se llama desde un contexto fuera de una conversación.
    app.add_handler(CallbackQueryHandler(cancel_operation, pattern='^pdf_config_cancel$'))

    logger.info("Módulo PDF Configuration registrado correctamente")