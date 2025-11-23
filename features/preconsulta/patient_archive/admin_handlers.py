# features/patient_archive/admin_handlers.py

import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, ContextTypes, CallbackQueryHandler, ConversationHandler, MessageHandler, filters, CommandHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest

from database import preconsulta_db
from common.decorators import admin_required
from common.helpers import escape_html
from . import keyboards
from features.preconsulta.components.logger import log_state, log_handler, log_func, log_ok, log_err, log_warn, log_msg
from utils.role_manager import RoleManager
from config import DB_PATH

logger = logging.getLogger(__name__)

# Helper para obtener doctor_id (multi-tenant)
role_manager = RoleManager(DB_PATH)

async def _get_doctor_id(update: Update) -> int:
    """Obtiene el doctor_id del usuario actual."""
    user_id = update.effective_user.id
    doctor = await role_manager.get_doctor_by_telegram_id(user_id)
    if doctor:
        return doctor[0]
    return None

# --- Estados para las conversaciones de este módulo ---
(AWAITING_SEARCH_TERM, EDITING_HUB, AWAITING_EDIT_VALUE) = range(3)



@admin_required
async def patient_archive_hub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Muestra los últimos pacientes completados y ofrece la opción de buscar.
    """
    query = update.callback_query
    await query.answer()
    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await query.edit_message_text("❌ Error: No se pudo identificar tu perfil de médico.")
        return

    latest_histories = await preconsulta_db.get_latest_completed_histories(doctor_id, limit=7)

    text = "📂 **Archivo de Pacientes**\n\n"
    keyboard = []
    keyboard.append([InlineKeyboardButton("🔍 Buscar Paciente por Nombre", callback_data="start_patient_search")])

    if not latest_histories:
        text += "Aún no hay informes completados."
    else:
        text += "Últimos informes completados:"
        for history in latest_histories:
            # Protección contra nombres vacíos
            patient_name = history.get('full_name', 'Nombre no disponible')
            visit_date = history.get('visit_date', 'Fecha desconocida')

            button_text = f"👤 {escape_html(patient_name)} ({visit_date})"
            callback_data = f"view_patient_history_{history['user_id']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    # --- ¡SINTAXIS CORREGIDA AQUÍ! ---
    # Los dos botones de navegación van en la misma fila (lista),
    # pero no anidados uno dentro del otro.
    keyboard.append([
        InlineKeyboardButton("🔙 ", callback_data="patient_management_hub"),
        InlineKeyboardButton("🏠 ", callback_data="main_menu")
    ])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

@admin_required
async def start_patient_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia la conversación para buscar un paciente."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🔍 Por favor, escribe el nombre (o parte del nombre) del paciente que deseas buscar.")
    return AWAITING_SEARCH_TERM

@admin_required
async def perform_patient_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibe el término de búsqueda, lo ejecuta y muestra los resultados."""
    search_term = update.message.text
    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await query.edit_message_text("❌ Error: No se pudo identificar tu perfil de médico.")
        return
    await update.message.delete()

    results = await preconsulta_db.search_completed_histories_by_name(doctor_id, search_term)

    if not results:
        text = f"❌ No se encontraron pacientes con informes completados que coincidan con '{escape_html(search_term)}'."
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver al Panel Admin", callback_data="main_menu")]])
    else:
        text = f"🔎 Resultados para '{escape_html(search_term)}':"
        reply_markup = keyboards.build_patient_search_results_keyboard(results)

    # El mensaje a editar es el que pedía el nombre
    try:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id, message_id=update.message.message_id - 1,
            text=text, reply_markup=reply_markup
        )
    except BadRequest: # Fallback si no se puede editar
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)

    return ConversationHandler.END

async def cancel_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Búsqueda cancelada.")
    # Aquí deberíamos volver al panel de admin de forma limpia
    return ConversationHandler.END

# --- HANDLER PARA VER EL HISTORIAL DE UN PACIENTE ---

@admin_required
async def view_patient_history(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int = None) -> None:
    """Muestra el historial de un paciente. Puede recibir el user_id directamente o desde el callback_data."""
    query = update.callback_query

    if query:
        await query.answer()

    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await query.edit_message_text("❌ Error: No se pudo identificar tu perfil de médico.")
        return

    if user_id is None:
        user_id = int(query.data.split('_')[-1])

    history_list = await preconsulta_db.get_patient_history_list(doctor_id, user_id)

    # Lógica para construir el mensaje
    if not history_list:
        text = "❌ No se encontraron informes para este paciente."
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver al Archivo", callback_data="patient_archive_hub")]])
    else:
        patient_name = (await preconsulta_db.get_history_details(history_list[0]['id'], doctor_id)).get('full_name')
        text = f"📂 **Historial de Consultas para {escape_html(patient_name)}**\n\nSelecciona un informe:"
        reply_markup = keyboards.build_patient_history_keyboard(history_list, user_id)

    # Lógica de envío/edición
    # Si tenemos un query y un mensaje asociado a él, lo editamos. Esto cubre todos los casos.
    if query and query.message:
        try:
            await query.edit_message_text(text=text, reply_markup=reply_markup)
        except BadRequest as e:
            # Si editar falla (ej. el texto no ha cambiado), simplemente lo ignoramos.
            if "Message is not modified" not in str(e):
                logger.error(f"Error al editar mensaje en view_patient_history: {e}")
    else:
        # Fallback por si la función se llama de una forma inesperada (ej. desde un comando).
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)

# --- CONVERSACIÓN DE EDICIÓN ---

@admin_required
async def start_editing_hub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log_func("start_editing_hub", "patient_archive")
    query = update.callback_query
    await query.answer()

    log_handler("start_editing_hub", update, "patient_archive")

    # FORZAR LIMPIEZA ANTES DE INICIAR
    context.user_data.clear()

    history_id = int(query.data.split('_')[-1])

    # Inicializar user_data fresco
    context.user_data['editing_history_id'] = history_id
    context.user_data['__conversation_state'] = 'EDITING_HUB'
    context.user_data['current_message_id'] = query.message.message_id  # Guardar ID actual

    log_state(context, "start_editing_hub", "patient_archive")

    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await query.edit_message_text("❌ Error: No se pudo identificar tu perfil de médico.")
        return
    details = await preconsulta_db.get_history_details(history_id, doctor_id)
    user_id = details.get('user_id')

    log_msg(f"Iniciando edición - History: {history_id}, User: {user_id}", "patient_archive")

    await query.edit_message_text(
        text=f"✏️ **Editando Informe #{history_id}**\nSelecciona la sección a modificar:",
        reply_markup=keyboards.get_editing_hub_keyboard(history_id, user_id)
    )
    return EDITING_HUB

@admin_required
async def prompt_for_edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log_func("prompt_for_edit_value", "patient_archive")
    query = update.callback_query
    await query.answer()

    log_handler("prompt_for_edit_value", update, "patient_archive")
    log_state(context, "prompt_for_edit_value", "patient_archive")

    try:
        _, history_id_str, field_to_edit = query.data.split(':', 2)
        history_id = int(history_id_str)
        log_msg(f"Solicitando edición - Field: {field_to_edit}, History: {history_id}", "patient_archive")
    except (ValueError, IndexError) as e:
        log_err("prompt_for_edit_value", e, f"Data: {query.data}", "patient_archive")
        await query.edit_message_text("❌ Error: Callback de edición inválido.")
        return EDITING_HUB

    context.user_data['editing_field'] = field_to_edit
    context.user_data['editing_history_id'] = history_id
    context.user_data['__conversation_state'] = 'AWAITING_EDIT_VALUE'
    context.user_data['current_message_id'] = query.message.message_id  # Guardar ID actual

    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await query.edit_message_text("❌ Error: No se pudo identificar tu perfil de médico.")
        return
    details = await preconsulta_db.get_history_details(history_id, doctor_id)
    current_value = details.get(field_to_edit, "No hay datos previos.")

    field_map = {
        "admin_physical_exam": "Examen Físico",
        "admin_ultrasound": "Ultrasonido",
        "admin_diagnosis": "Diagnóstico",
        "admin_plan": "Plan",
        "admin_observations": "Observaciones"
    }

    # CASO ESPECIAL: Si es el plan, mostrar items seleccionables
    if field_to_edit == "admin_plan":
        # Parsear los items del plan (dividir por \n)
        plan_items = [item.strip() for item in current_value.strip().split('\n') if item.strip()]
        
        if not plan_items:
            text_prompt = (
                f"<b>Editando:</b> Plan\n\n"
                f"<b>No hay items en el plan actual.</b>\n\n"
                f"Por favor, envía el nuevo contenido para este campo."
            )
            await query.edit_message_text(text=text_prompt, parse_mode=ParseMode.HTML)
            return AWAITING_EDIT_VALUE
        
        # Mostrar items como lista seleccionable
        text_prompt = (
            f"<b>Editando:</b> Plan\n\n"
            f"<b>Items del Plan Actual:</b>\n\n"
        )
        # Construir lista numerada de items
        items_text = "\n".join([f"{i+1}. {escape_html(item[:60])}{'...' if len(item) > 60 else ''}" for i, item in enumerate(plan_items)])
        text_prompt += items_text + "\n\n"
        text_prompt += "Selecciona el item que deseas modificar:"
        
        # Crear teclado con botones para cada item
        keyboard = []
        for i, item in enumerate(plan_items):
            # Limitar el texto del botón a 50 caracteres
            button_text = f"{i+1}. {item[:47]}{'...' if len(item) > 47 else ''}"
            callback_data = f"edit_plan_item:{history_id}:{i}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Botón para cancelar
        keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data=f"start_editing_{history_id}")])
        
        await query.edit_message_text(
            text=text_prompt,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
        # Guardar los items del plan en user_data para uso posterior
        context.user_data['plan_items'] = plan_items
        return EDITING_HUB  # Mantener en EDITING_HUB, no pasar a AWAITING_EDIT_VALUE todavía
    
    # Para otros campos, comportamiento normal
    text_prompt = (
        f"<b>Editando:</b> {field_map.get(field_to_edit, 'Campo Desconocido')}\n\n"
        f"<b>Valor Actual:</b>\n<pre>{escape_html(current_value)}</pre>\n\n"
        f"Por favor, envía el nuevo contenido para este campo."
    )

    await query.edit_message_text(text=text_prompt, parse_mode=ParseMode.HTML)
    return AWAITING_EDIT_VALUE

@admin_required
async def select_plan_item_to_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Muestra el item seleccionado del plan y pide el nuevo valor."""
    log_func("select_plan_item_to_edit", "patient_archive")
    query = update.callback_query
    await query.answer()
    
    try:
        _, history_id_str, item_index_str = query.data.split(':')
        history_id = int(history_id_str)
        item_index = int(item_index_str)
    except (ValueError, IndexError) as e:
        log_err("select_plan_item_to_edit", e, f"Data: {query.data}", "patient_archive")
        await query.edit_message_text("❌ Error: Callback inválido.")
        return EDITING_HUB
    
    # Obtener los items del plan guardados en user_data
    plan_items = context.user_data.get('plan_items', [])
    if not plan_items or item_index >= len(plan_items):
        await query.edit_message_text("❌ Error: Item no encontrado.")
        return EDITING_HUB
    
    # Guardar información para receive_edited_value
    context.user_data['editing_history_id'] = history_id
    context.user_data['editing_field'] = 'admin_plan'
    context.user_data['editing_plan_item_index'] = item_index
    context.user_data['__conversation_state'] = 'AWAITING_EDIT_VALUE'
    context.user_data['current_message_id'] = query.message.message_id
    
    # Mostrar el item actual y pedir el nuevo valor
    current_item = plan_items[item_index]
    text_prompt = (
        f"<b>Editando Item #{item_index + 1} del Plan</b>\n\n"
        f"<b>Valor Actual:</b>\n<pre>{escape_html(current_item)}</pre>\n\n"
        f"Por favor, envía el nuevo contenido para este item."
    )
    
    await query.edit_message_text(text=text_prompt, parse_mode=ParseMode.HTML)
    return AWAITING_EDIT_VALUE

# --- REGISTRO DE HANDLERS ---
@admin_required
async def receive_edited_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log_func("receive_edited_value", "patient_archive")
    new_value = update.message.text
    history_id = context.user_data.get('editing_history_id')
    field = context.user_data.get('editing_field')

    log_msg(f"Mensaje recibido - History: {history_id}, Field: {field}, Text: {new_value[:50]}...", "patient_archive")
    log_state(context, "receive_edited_value", "patient_archive")

    # Borramos el mensaje del usuario
    await update.message.delete()

    if not all([history_id, field]):
        log_err("receive_edited_value", Exception("Sesión expirada"), "Faltan history_id o field", "patient_archive")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Sesión de edición expirada.")
        return ConversationHandler.END

    # CASO ESPECIAL: Si estamos editando un item específico del plan
    if field == 'admin_plan' and 'editing_plan_item_index' in context.user_data:
        item_index = context.user_data['editing_plan_item_index']
        plan_items = context.user_data.get('plan_items', [])
        
        if item_index < len(plan_items):
            # Actualizar solo el item seleccionado
            plan_items[item_index] = new_value
            # Reconstruir el plan completo con los items actualizados
            updated_plan = '\n'.join(plan_items)
            # Actualizar en la base de datos
            success = await preconsulta_db.update_history_field(history_id, field, updated_plan)
            # Limpiar el índice del item editado
            context.user_data.pop('editing_plan_item_index', None)
        else:
            success = False
    else:
        # Comportamiento normal para otros campos
        success = await preconsulta_db.update_history_field(history_id, field, new_value)

    if success:
        text_feedback = "✅ ¡Campo actualizado con éxito!"
        log_ok("receive_edited_value", f"History: {history_id}, Field: {field}", "patient_archive")
    else:
        text_feedback = "❌ Error al actualizar el campo."
        log_err("receive_edited_value", Exception("Error BD"), f"History: {history_id}, Field: {field}", "patient_archive")

    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await query.edit_message_text("❌ Error: No se pudo identificar tu perfil de médico.")
        return
    details = await preconsulta_db.get_history_details(history_id, doctor_id)
    user_id = details.get('user_id') if details else None

    # USAR EL MENSAJE GUARDADO en lugar de calcular el ID
    message_id_to_edit = context.user_data.get('current_message_id')

    edit_success = False
    if message_id_to_edit:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=message_id_to_edit,
                text=f"{text_feedback}\n\n✏️ **Editando Informe #{history_id}**\nSelecciona otra sección o finaliza.",
                reply_markup=keyboards.get_editing_hub_keyboard(history_id, user_id)
            )
            edit_success = True
            log_msg(f"✅ Mensaje {message_id_to_edit} editado exitosamente", "patient_archive")
        except BadRequest as e:
            log_err("receive_edited_value", e, f"No se pudo editar mensaje {message_id_to_edit}", "patient_archive")
            edit_success = False

    # FALLBACK: enviar nuevo mensaje
    if not edit_success:
        log_msg("Enviando nuevo mensaje como fallback", "patient_archive")
        new_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"{text_feedback}\n\n✏️ **Editando Informe #{history_id}**\nSelecciona otra sección o finaliza.",
            reply_markup=keyboards.get_editing_hub_keyboard(history_id, user_id)
        )
        # Actualizar el ID del mensaje actual para futuras operaciones
        context.user_data['current_message_id'] = new_message.message_id

    context.user_data['__conversation_state'] = 'EDITING_HUB'
    context.user_data.pop('editing_field', None)

    log_msg("Regresando a EDITING_HUB", "patient_archive")
    return EDITING_HUB

async def cancel_editing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela el proceso de edición y redirige apropiadamente - VERSIÓN MEJORADA."""
    log_func("cancel_editing", "patient_archive")

    query = update.callback_query
    if query:
        await query.answer()
        log_msg(f"Cancelando edición desde callback: {query.data}", "patient_archive")

        # Dependiendo del callback, redirigir a diferentes lugares
        if query.data.startswith('view_patient_history_'):
            # Redirigir al historial del paciente
            await view_patient_history(update, context)
        elif query.data == 'main_menu':
            # Redirigir al menú principal
            from features.main_menu import main_menu
            await main_menu(update, context)
        elif query.data == 'patient_management_hub':
            # Redirigir al hub de gestión de pacientes
            from features.preconsultas_admin.admin_handlers import patient_management_hub
            await patient_management_hub(update, context)
        elif query.data == 'patient_archive_hub':
            # Redirigir al archivo de pacientes
            await patient_archive_hub(update, context)
        else:
            # Redirigir por defecto al archivo de pacientes
            await patient_archive_hub(update, context)
    else:
        log_msg("Cancelando edición desde comando/mensaje", "patient_archive")
        # Por defecto, redirigir al archivo de pacientes
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Edición cancelada.")

    # Limpiar user_data
    context.user_data.clear()
    log_msg("User_data limpiado completamente", "patient_archive")

    return ConversationHandler.END

@admin_required
async def force_cancel_editing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fuerza la cancelación de cualquier edición activa cuando se navega a otros menús."""
    log_func("force_cancel_editing", "patient_archive")

    # Verificar si hay una edición activa
    if context.user_data.get('editing_history_id') or context.user_data.get('__conversation_state'):
        log_msg("Forzando cancelación de edición activa por navegación", "patient_archive")
        context.user_data.clear()
        log_ok("force_cancel_editing", "Edición cancelada por navegación", "patient_archive")

    # Redirigir al destino original
    query = update.callback_query
    await query.answer()

    # Determinar a dónde redirigir basado en el callback_data
    if query.data == "main_menu":
        from features.main_menu import main_menu
        await main_menu(update, context)
    elif query.data == "patient_management_hub":
        from features.preconsultas_admin.admin_handlers import patient_management_hub
        await patient_management_hub(update, context)
    elif query.data == "patient_archive_hub":
        await patient_archive_hub(update, context)
    else:
        log_warn("force_cancel_editing", f"Callback no manejado: {query.data}", "patient_archive")

@admin_required
async def finish_editing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Finaliza el proceso de edición de manera limpia y redirige al historial del paciente."""
    log_func("finish_editing", "patient_archive")
    query = update.callback_query
    await query.answer()

    history_id = int(query.data.split(':')[-1])

    log_msg(f"Finalizando edición para history: {history_id}", "patient_archive")
    log_state(context, "finish_editing", "patient_archive")

    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await query.edit_message_text("❌ Error: No se pudo identificar tu perfil de médico.")
        return
    details = await preconsulta_db.get_history_details(history_id, doctor_id)
    user_id = details.get('user_id') if details else None

    context.user_data.clear()
    log_msg("User_data limpiado completamente al finalizar edición", "patient_archive")

    if user_id:
        # ¡CORREGIDO! Ya no borramos el mensaje.
        # Simplemente llamamos a la función que lo va a editar.
        await view_patient_history(update, context, user_id=user_id)
    else:
        await patient_archive_hub(update, context)

    return ConversationHandler.END

def register(app: Application):
    log_msg("Registrando handlers de patient_archive", "patient_archive")

    search_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_patient_search, pattern='^start_patient_search$')],
        states={ AWAITING_SEARCH_TERM: [MessageHandler(filters.TEXT & ~filters.COMMAND, perform_patient_search)] },
        fallbacks=[CommandHandler('cancelar', cancel_search)]
    )

    edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_editing_hub, pattern=r'^start_editing_')],
        states={
            EDITING_HUB: [
                CallbackQueryHandler(start_editing_hub, pattern=r'^start_editing_'),  # Permitir volver al hub de edición
                CallbackQueryHandler(prompt_for_edit_value, pattern=r'^edit_field:'),
                CallbackQueryHandler(select_plan_item_to_edit, pattern=r'^edit_plan_item:'),  # Nuevo handler para seleccionar item del plan
                CallbackQueryHandler(cancel_editing, pattern=r'^main_menu$'),
                CallbackQueryHandler(cancel_editing, pattern=r'^patient_management_hub$'),
                CallbackQueryHandler(cancel_editing, pattern=r'^patient_archive_hub$'),
                CallbackQueryHandler(cancel_editing, pattern=r'^list_histories_'),
                # NUEVO: Permitir salir con view_patient_history desde EDITING_HUB
                CallbackQueryHandler(cancel_editing, pattern=r'^view_patient_history_'),
            ],
            AWAITING_EDIT_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_edited_value),
                CommandHandler('cancelar', cancel_editing),
                CallbackQueryHandler(cancel_editing, pattern=r'^main_menu$'),
                CallbackQueryHandler(cancel_editing, pattern=r'^patient_management_hub$'),
                # NUEVO: Permitir salir con view_patient_history desde AWAITING_EDIT_VALUE
                CallbackQueryHandler(cancel_editing, pattern=r'^view_patient_history_'),
            ]
        },
        fallbacks=[
            CommandHandler('cancelar', cancel_editing),
            CallbackQueryHandler(cancel_editing, pattern=r'^main_menu$'),
            CallbackQueryHandler(cancel_editing, pattern=r'^patient_management_hub$'),
            CallbackQueryHandler(cancel_editing, pattern=r'^patient_archive_hub$'),
            CallbackQueryHandler(cancel_editing, pattern=r'^list_histories_'),
            CallbackQueryHandler(cancel_editing, pattern=r'^view_patient_history_'),  # Ya existe
            # ELIMINAR: CallbackQueryHandler(view_patient_history, pattern=r'^finish_editing_')
        ]
    )

    app.add_handler(CallbackQueryHandler(patient_archive_hub, pattern=r'^patient_archive_hub$'))
    app.add_handler(search_conv)
    app.add_handler(edit_conv)
    app.add_handler(CallbackQueryHandler(view_patient_history, pattern=r'^view_patient_history_'))
    app.add_handler(CallbackQueryHandler(finish_editing, pattern=r'^finish_editing:'))

    log_ok("register", "Todos los handlers de patient_archive registrados", "patient_archive")
