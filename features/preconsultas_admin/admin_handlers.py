# features/preconsultas_admin/admin_handlers.py

import asyncio
import json
import logging
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.error import BadRequest
from common import pdf_generator


from database import preconsulta_db
from common.decorators import admin_required
from common.helpers import escape_html
from . import keyboards
from .exam_flow.exam_flow_engine import start_exam_flow, process_exam_input, AWAITING_EXAM_INPUT
from features.preconsulta.components.logger import log_func, log_handler, log_state, log_msg, log_ok, log_err, log_warn
from .states import *
from utils.role_manager import RoleManager
from config import DB_PATH

logger = logging.getLogger(__name__)

# Define el número de items por página
ITEMS_PER_PAGE = 10

# Helper para obtener doctor_id (multi-tenant)
role_manager = RoleManager(DB_PATH)

async def _get_doctor_id(update: Update) -> int:
    """Obtiene el doctor_id del usuario actual."""
    user_id = update.effective_user.id
    doctor = await role_manager.get_doctor_by_telegram_id(user_id)
    if doctor:
        return doctor[0]
    return None


@admin_required
async def dismiss_preconsulta_notification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Permite que el médico marque en cuenta la notificación de una preconsulta."""
    query = update.callback_query
    if not query:
        return

    await query.answer("🗑️ Notificación marcada en cuenta.", show_alert=False)
    try:
        await query.message.delete()
    except Exception as exc:
        logger.warning("No se pudo eliminar la notificación de preconsulta: %s", exc)

@admin_required
async def generate_summary_pdf_hub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Genera el PDF del Informe Médico resumido, lo guarda en caché y muestra las opciones.
    """
    query = update.callback_query
    await query.answer()

    history_id = int(query.data.split('_')[-1])

    await query.edit_message_text("⏳ Generando Informe Médico resumido, por favor espera...")

    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await query.edit_message_text("❌ Error: No se pudo identificar tu perfil de médico.")
        return
    
    report_data = await preconsulta_db.get_history_details(history_id, doctor_id)

    if not report_data:
        await query.edit_message_text("❌ Error: No se encontraron los datos del informe.")
        return

    # 1. Llamar a la nueva función generadora de PDF resumido
    pdf_bytes = await pdf_generator.generate_summary_report(report_data, doctor_id)

    # 2. Enviar el documento para obtener su file_id (caché)
    sent_doc = await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=InputFile(pdf_bytes, filename=f"Informe_Resumido_{history_id}.pdf"),
        caption=f"Cache interno para informe resumido #{history_id}"
    )
    pdf_file_id = sent_doc.document.file_id

    # 3. Borrar el mensaje de envío para mantener el chat limpio
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_doc.message_id)

    # 4. Guardar el file_id en bot_data para reutilizarlo
    # Usamos una clave diferente para no sobrescribir el PDF completo
    context.bot_data.setdefault('summary_pdf_file_ids', {})[history_id] = pdf_file_id

    await query.edit_message_text("✅ Informe Médico resumido generado con éxito.")
    await asyncio.sleep(2)

    patient_name = report_data.get('full_name', 'el paciente')
    text = (
        f"✅ **¡Informe Médico Resumido Generado!**\n\n"
        f"El informe para <b>{escape_html(patient_name)}</b> ha sido creado. ¿Qué deseas hacer ahora?"
    )

    # 5. Lógica para construir los callbacks de los botones de acción
    parts = query.data.split('_')
    back_callback = "patient_archive_hub"
    back_text = "🔙 "
    try:
        source = parts[3]
        param = parts[4] if len(parts) > 4 else '0'
        if source == 'pendinglist':
            back_callback = f"list_histories_{param}"
            back_text = "🔙 "
        elif source == 'patienthistory':
            back_callback = f"patient_history_{param}"
            back_text = "🔙 "
        elif source == 'completion':
            back_callback = f"view_history_{history_id}_pendinglist_{param}"
            back_text = "🔙 "
    except IndexError:
        pass

    # Usamos callbacks distintos para las acciones del PDF resumido
    download_callback = f"download_summary_pdf_{history_id}"
    send_callback = f"send_summary_to_patient_{history_id}"

    keyboard = [
        [
            InlineKeyboardButton("✉️ Enviar al Paciente", callback_data=send_callback),
            InlineKeyboardButton("📥 Descargar", callback_data=download_callback)
        ],
        [
            InlineKeyboardButton(back_text, callback_data=back_callback),
            InlineKeyboardButton("🏠 ", callback_data="main_menu")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


@admin_required
async def patient_management_hub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra el submenú para gestionar preconsultas, archivo y ahora logos."""
    query = update.callback_query
    await query.answer()

    text = "📋 **Gestión de Pacientes y Preconsultas**\n\nSelecciona una opción:"
    keyboard = [
        [InlineKeyboardButton("📝 Ver Preconsultas Pendientes", callback_data="list_histories_0")],
        [InlineKeyboardButton("📂 Archivo de Pacientes (Buscar)", callback_data="patient_archive_hub")],

        [InlineKeyboardButton("🏠 ", callback_data="main_menu")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def start_consultation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia la conversación para completar el informe, preguntando primero si se usará la plantilla."""
    query = update.callback_query
    await query.answer()

    history_id = int(query.data.split('_')[-1])
    
    # Limpiar datos de sesiones anteriores para evitar mezclas si se reingresa
    keys_to_clear = [
        'diagnosis_list', 'plan_list', 'physical_exam_notes', 'admin_physical_exam',
        'ultrasound_notes', 'admin_ultrasound', 'diagnosis_notes', 'admin_diagnosis',
        'plan_notes', 'admin_plan', 'observation_notes', 'admin_observations'
    ]
    for k in keys_to_clear:
        context.user_data.pop(k, None)

    context.user_data['current_history_id'] = history_id
    context.user_data['consultation_anchor_message_id'] = query.message.message_id

    # Preparamos la pregunta inicial
    text = "✍️ **Paso 1/5: Examen Físico**\n\n¿Quieres utilizar la plantilla guiada para rellenar esta sección?"
    keyboard = [
        [
            InlineKeyboardButton("✅ Sí, usar plantilla", callback_data="exam_choice_yes"),
            InlineKeyboardButton("⌨️ No, escribir manualmente", callback_data="exam_choice_no")
        ],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancel_consultation_conv")]
    ]

    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

    # Transicionamos al nuevo estado de decisión
    return AWAITING_EXAM_TEMPLATE_CHOICE

# --- AÑADE ESTA NUEVA FUNCIÓN ---
async def handle_exam_template_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja la elección del admin y bifurca al sub-flujo o a la entrada de texto."""
    query = update.callback_query
    await query.answer()
    choice = query.data
    if choice == "exam_choice_yes":
        from .exam_flow.exam_flow_engine import start_exam_flow
        return await start_exam_flow(update, context)
    elif choice == "exam_choice_no":
        text = "✍️ Por favor, introduce los hallazgos del examen físico."
        await query.edit_message_text(text=text, parse_mode=ParseMode.HTML)
        return AWAITING_PHYSICAL_EXAM

# --- FUNCIÓN REFACTORIZADA Y RENOMBRADA ---
async def transition_to_ultrasound(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Función de transición que se activa después de que el examen físico se completa
    (ya sea manual o por plantilla) y avanza al paso del ultrasonido.
    """
    # Si viene de una entrada manual (mensaje de texto), guardamos los datos.
    if update.message and update.message.text:
        context.user_data['admin_physical_exam'] = update.message.text
        await update.message.delete()

    # Si viene del sub-flujo, el dato 'admin_physical_exam' ya fue generado y guardado.

    # Preparamos y mostramos la siguiente pregunta
    text = (
        "✍️ **Paso 2/5: Ultrasonido Transvaginal**\n\n"
        "Introduce los resultados del ultrasonido."
    )
    message_id = context.user_data.get('consultation_anchor_message_id')
    try:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=message_id,
            text=text
        )
    except BadRequest as e:
        logger.warning(f"No se pudo editar el mensaje ancla en transition_to_ultrasound: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    # Transicionamos al siguiente estado del flujo principal
    return AWAITING_ULTRASOUND




async def process_exam_flow_result(update, context):
    """
    Esta función se activa cuando el motor del examen físico devuelve "END_SUBFLOW".
    Recibe el control y continúa con el siguiente paso del flujo principal.
    """
    # El resumen del examen ya fue guardado en 'admin_physical_exam' por la última acción del sub-flujo.
    # Ahora, simplemente continuamos con el siguiente paso: Ultrasonido.
    text = "✍️ **Paso 2/5: Ultrasonido Transvaginal**\n\nIntroduce los resultados del ultrasonido."
    message_id = context.user_data.get('consultation_anchor_message_id')
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=message_id, text=text)
    return AWAITING_ULTRASOUND


# --- Placeholder para las demás funciones que construiremos ---
async def receive_ultrasound(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibe el ultrasonido y pide el PRIMER ítem del diagnóstico."""
    context.user_data['ultrasound_notes'] = update.message.text
    await update.message.delete()

    # Inicializamos la lista de diagnósticos
    context.user_data['diagnosis_list'] = []

    text = "✍️ **Paso 3/4: Diagnóstico**\n\nIntroduce el <b>primer</b> diagnóstico:"

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['consultation_anchor_message_id'],
        text=text,
        parse_mode=ParseMode.HTML
    )
    return ADDING_DIAGNOSIS_ITEM


async def receive_diagnosis_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibe un ítem de diagnóstico, lo añade a la lista y pregunta si quiere añadir más."""
    item = update.message.text
    context.user_data['diagnosis_list'].append(item)
    await update.message.delete()

    # Mostramos los ítems ya añadidos para que la doctora tenga contexto
    current_items_text = "\n".join(f"{i+1}) {d}" for i, d in enumerate(context.user_data['diagnosis_list']))

    text = (
        "<b>Diagnósticos añadidos:</b>\n"
        f"<code>{current_items_text}</code>\n\n"
        "¿Deseas añadir otro diagnóstico o continuar con el Plan?"
    )

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['consultation_anchor_message_id'],
        text=text,
        reply_markup=keyboards.get_add_another_keyboard('diagnóstico'),
        parse_mode=ParseMode.HTML
    )
    return AWAITING_DIAGNOSIS # Estado de decisión

async def add_another_diagnosis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """El admin quiere añadir otro diagnóstico, se lo pedimos."""
    query = update.callback_query
    await query.answer()

    next_item_num = len(context.user_data.get('diagnosis_list', [])) + 1
    text = f"Introduce el diagnóstico número <b>{next_item_num}</b>:"

    await query.edit_message_text(text=text, parse_mode=ParseMode.HTML)
    return ADDING_DIAGNOSIS_ITEM # Volvemos al estado de añadir ítem


async def start_plan_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Finaliza la recogida de diagnósticos y empieza la de Plan."""
    query = update.callback_query
    await query.answer()

    # Guardamos la lista de diagnósticos como un string con saltos de línea
    context.user_data['diagnosis_notes'] = "\n".join(context.user_data.get('diagnosis_list', []))

    # Inicializamos la lista del plan
    context.user_data['plan_list'] = []

    text = "✍️ **Paso 4/4: Plan de Tratamiento**\n\nIntroduce el <b>primer</b> punto del plan:"

    await query.edit_message_text(text=text, parse_mode=ParseMode.HTML)
    return ADDING_PLAN_ITEM


async def receive_plan_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibe un ítem del plan, lo añade a la lista y pregunta si quiere añadir más."""
    item = update.message.text
    context.user_data['plan_list'].append(item)
    await update.message.delete()

    current_items_text = "\n".join(f"• {p}" for p in context.user_data['plan_list'])

    text = (
        "<b>Puntos del Plan añadidos:</b>\n"
        f"<code>{current_items_text}</code>\n\n"
        "¿Deseas añadir otro punto o finalizar el informe?"
    )

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['consultation_anchor_message_id'],
        text=text,
        reply_markup=keyboards.get_add_another_keyboard('plan'),
        parse_mode=ParseMode.HTML
    )
    return AWAITING_PLAN # Estado de decisión


async def add_another_plan_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """El admin quiere añadir otro punto al plan."""
    query = update.callback_query
    await query.answer()

    next_item_num = len(context.user_data.get('plan_list', [])) + 1
    text = f"Introduce el punto del plan número <b>{next_item_num}</b>:"

    await query.edit_message_text(text=text, parse_mode=ParseMode.HTML)
    return ADDING_PLAN_ITEM

async def receive_plan_and_finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibe el plan, guarda todo en la BD y muestra opciones para generar el PDF."""
    context.user_data['plan_notes'] = update.message.text
    await update.message.delete()

    ud = context.user_data
    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Error: No se pudo identificar tu perfil de médico."
        )
        return ConversationHandler.END
    history_id = ud.get('current_history_id')

    admin_data = {
        'consultation_type': ud.get('consultation_type'),
        'admin_physical_exam': ud.get('physical_exam_notes'),
        'admin_ultrasound': ud.get('ultrasound_notes'),
        'admin_diagnosis': ud.get('diagnosis_notes'),
        'admin_plan': ud.get('plan_notes')
    }

    success = await preconsulta_db.complete_history(history_id, doctor_id, admin_data)

    if success:
        final_text = "✅ ¡Informe médico completado y guardado con éxito!"
        # --- ¡NUEVOS BOTONES! ---
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Generar Informe (PDF)", callback_data=f"generate_summary_pdf_{history_id}")],
            [InlineKeyboardButton("🔙 ", callback_data="list_histories_0")]
        ])
    else:
        final_text = "❌ Hubo un error al guardar el informe."
        reply_markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 ", callback_data="list_histories_0")
        ]])

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=ud['consultation_anchor_message_id'],
        text=final_text,
        reply_markup=reply_markup
    )

    context.user_data.clear()
    return ConversationHandler.END


@admin_required
async def generate_pdf_hub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Punto de entrada para la generación de PDF con flujo optimizado.
    """
    query = update.callback_query
    await query.answer()

    parts = query.data.split('_')
    history_id = int(parts[2])

    back_callback = "patient_archive_hub"
    back_text = "🔙 "

    try:
        source = parts[3]
        param = parts[4] if len(parts) > 4 else None
        if source == 'patientarchive':
            back_callback = "patient_archive_hub"
            back_text = "🔙 "
        elif source == 'pendinglist':
            back_callback = f"list_histories_{param}"
            back_text = "🔙 "
    except IndexError:
        pass

    await query.edit_message_text("⏳ Generando Historia Médica completa, por favor espera...")

    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await query.edit_message_text("❌ Error: No se pudo identificar tu perfil de médico.")
        return
    report_data = await preconsulta_db.get_history_details(history_id, doctor_id)
    if not report_data:
        await query.edit_message_text("❌ Error: No se encontraron los datos del informe.")
        return

    # Generar la HISTORIA MÉDICA COMPLETA (tamaño oficio)
    pdf_bytes = await pdf_generator.generate_medical_report(report_data, doctor_id)

    sent_doc = await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=InputFile(pdf_bytes, filename=f"Historia_Medica_{history_id}.pdf"),
        caption=f"Cache interno para historia médica completa #{history_id}"
    )
    pdf_file_id = sent_doc.document.file_id
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_doc.message_id)

    # Usar la clave de caché para PDFs de historia completa
    context.bot_data.setdefault('pdf_file_ids', {})[history_id] = pdf_file_id
    await query.edit_message_text("✅ Historia Médica generada con éxito...")
    await asyncio.sleep(2)

    patient_name = report_data.get('full_name', 'el paciente')
    text = (
        f"✅ **¡Historia Médica Generada!**\n\n"
        f"La historia médica completa para <b>{escape_html(patient_name)}</b> ha sido creada. ¿Qué deseas hacer ahora?"
    )

    # Usar los callbacks para la historia médica completa
    download_pdf_callback = f"download_pdf_{history_id}"
    send_to_patient_callback = f"send_to_patient_{history_id}"

    if back_callback == "patient_archive_hub":
        download_pdf_callback += f"_patientarchive"
        send_to_patient_callback += f"_patientarchive"
    elif back_callback.startswith("list_histories_"):
        page = back_callback.split('_')[-1]
        download_pdf_callback += f"_pendinglist_{page}"
        send_to_patient_callback += f"_pendinglist_{page}"

    # MODIFICACIÓN: Agregar botón "Menú Principal"
    keyboard = [
        [
            InlineKeyboardButton("✉️ Enviar al Paciente", callback_data=send_to_patient_callback),
            InlineKeyboardButton("📥 Descargar PDF", callback_data=download_pdf_callback)
        ],
        [
            InlineKeyboardButton(back_text, callback_data=back_callback),
            InlineKeyboardButton("🏠", callback_data="main_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

@admin_required
async def download_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Recupera el file_id de un PDF previamente generado y lo envía
    al admin que presiona el botón.
    """
    log_func("download_pdf", "preconsultas_admin")
    query = update.callback_query
    parts = query.data.split('_')

    try:
        history_id = int(parts[2])
        log_msg(f"Solicitud de descarga de PDF para history: {history_id}", "preconsultas_admin")
    except (ValueError, IndexError) as e:
        log_err("download_pdf", e, f"Data: {query.data}", "preconsultas_admin")
        await query.answer("❌ Error: ID de historia no válido.", show_alert=True)
        return

    pdf_file_id = context.bot_data.get('pdf_file_ids', {}).get(history_id)
    if not pdf_file_id:
        log_warn("download_pdf", f"No se encontró file_id para history: {history_id}", "preconsultas_admin")
        await query.answer("❌ No se pudo encontrar el PDF generado. Intenta re-generarlo.", show_alert=True)
        return

    try:
        await query.answer("📥 Enviando tu PDF...")
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=pdf_file_id,
            caption=f"Informe Médico para la historia #{history_id}."
        )
        log_ok("download_pdf", f"PDF para history {history_id} enviado al admin.", "preconsultas_admin")
    except Exception as e:
        log_err("download_pdf", e, f"No se pudo enviar el PDF con file_id para history {history_id}", "preconsultas_admin")
        await query.answer("❌ Hubo un error al enviar el archivo PDF.", show_alert=True)


@admin_required
async def send_pdf_to_patient(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía el PDF previamente generado al paciente."""
    query = update.callback_query
    await query.answer()

    parts = query.data.split('_')
    try:
        history_id = int(parts[2])
    except (ValueError, IndexError):
        await query.answer("❌ Error: ID de historia no válido.", show_alert=True)
        return

    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await query.answer("❌ Error: No se pudo identificar tu perfil de médico.", show_alert=True)
        return
    pdf_file_id = context.bot_data.get('pdf_file_ids', {}).get(history_id)
    history_details = await preconsulta_db.get_history_details(history_id, doctor_id)

    if not history_details or not pdf_file_id:
        await query.answer("❌ Error: No se pudo encontrar la historia o el PDF.", show_alert=True)
        return

    patient_id = history_details.get('user_id')
    try:
        await context.bot.send_document(
            chat_id=patient_id,
            document=pdf_file_id,
            caption="Hola, la Dra. Herrera te envía tu informe médico."
        )
        await query.answer("✅ Informe enviado al paciente con éxito.", show_alert=True)
    except Exception as e:
        logger.error(f"Error al enviar PDF al paciente {patient_id}: {e}")
        await query.answer("❌ Hubo un error al intentar enviar el informe.", show_alert=True)

@admin_required
async def confirm_delete_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra un mensaje de confirmación antes de eliminar una preconsulta."""
    query = update.callback_query
    await query.answer()

    history_id = int(query.data.split('_')[-1])

    # Obtenemos el callback de "Volver" desde la vista de detalles para poder regresar
    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await query.edit_message_text("❌ Error: No se pudo identificar tu perfil de médico.")
        return
    details = await preconsulta_db.get_history_details(history_id, doctor_id)
    back_callback = f"view_history_{history_id}_pendinglist_0" # Un fallback seguro
    if details:
        # Reconstruimos el callback_data de la vista anterior para un "cancelar" limpio
        # Esto es un poco complejo, pero asegura que volvamos exactamente a donde estábamos.
        # Por simplicidad, construiremos un callback de volver a la lista de pendientes.
        current_page = 0 # Asumimos página 0 si no podemos deducirla
        # Intentamos obtener la página del último query, si lo guardamos
        if context.user_data.get('last_list_page'):
            current_page = context.user_data['last_list_page']
        back_callback = f"view_history_{history_id}_pendinglist_{current_page}"


    text = "⚠️ **¿Estás seguro/a?**\n\nEsta acción eliminará permanentemente la preconsulta. No se puede deshacer."
    keyboard = [
        [
            InlineKeyboardButton("✅ Sí, eliminar", callback_data=f"execute_delete_history_{history_id}"),
            InlineKeyboardButton("❌ No, cancelar", callback_data=back_callback)
        ]
    ]

    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

@admin_required
async def execute_delete_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ejecuta la eliminación de la preconsulta y vuelve a la lista."""
    query = update.callback_query
    await query.answer()

    history_id = int(query.data.split('_')[-1])

    success = await preconsulta_db.delete_history(history_id)

    if success:
        await query.edit_message_text("✅ Preconsulta eliminada con éxito.")
    else:
        await query.edit_message_text("❌ Hubo un error al intentar eliminar la preconsulta.")

    await asyncio.sleep(2)

    # Llamamos a la función de la lista, pasándole la página 0 explícitamente
    await list_medical_histories(update, context, page=0)


@admin_required
async def list_medical_histories(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = None) -> None:
    """
    Muestra la lista paginada de preconsultas completadas.
    Ahora puede recibir la página directamente como argumento.
    """
    query = update.callback_query
    await query.answer()

    # Si la página no se pasa como argumento (ej. viene de un botón de paginación),
    # la extraemos del callback_data. Si se pasa (ej. desde execute_delete_history),
    # usamos el valor proporcionado.
    if page is None:
        try:
            page = int(query.data.split('_')[-1])
        except (ValueError, IndexError):
            page = 0

    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await query.edit_message_text("❌ Error: No se pudo identificar tu perfil de médico.")
        return
    offset = page * ITEMS_PER_PAGE

    histories = await preconsulta_db.get_all_histories(doctor_id, offset=offset, limit=ITEMS_PER_PAGE)

    if not histories and page == 0:
        text = "✅ No hay preconsultas pendientes por el momento."
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 ", callback_data="patient_management_hub")]
        ])
    else:
        text = "📋 **Preconsultas Pendientes**\n\nSelecciona una para ver los detalles:"
        reply_markup = keyboards.build_histories_list_keyboard(histories, current_page=page)

    await query.edit_message_text(text=text, reply_markup=reply_markup)


async def descartar_pdf_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el botón de descartar PDF."""
    query = update.callback_query
    await query.answer()

    parts = query.data.split('_')

    # CORRECCIÓN: Extraer history_id de la posición correcta
    try:
        history_id = int(parts[2])
    except (ValueError, IndexError):
        await query.answer("❌ Error: ID de historia no válido.", show_alert=True)
        return

    try:
        # Eliminar el mensaje que contiene el PDF
        await query.message.delete()
        await query.answer("✅ PDF descartado correctamente")
    except Exception as e:
        await query.answer("❌ No se pudo eliminar el mensaje", show_alert=True)


async def ask_for_observations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Finaliza la recogida del plan y pide al admin que introduzca las observaciones.
    """
    query = update.callback_query
    await query.answer()

    # Guardamos la lista del plan como un string con saltos de línea
    context.user_data['plan_notes'] = "\n".join(context.user_data.get('plan_list', []))

    # Editamos el mensaje para pedir el último dato
    await query.edit_message_text(
        text="✍️ **Paso Final: Observaciones**\n\n"
             "Introduce cualquier observación adicional. Si no hay, escribe 'Ninguna'."
    )

    # Pasamos al nuevo estado que espera el texto de las observaciones
    return AWAITING_OBSERVATIONS
async def receive_observations_and_finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Recibe las observaciones, guarda TODA la información en la BD y finaliza la conversación.
    """
    # Guardamos el último dato
    context.user_data['observation_notes'] = update.message.text
    await update.message.delete()

    # --- Aquí va toda la lógica que antes estaba en finish_consultation ---
    ud = context.user_data
    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Error: No se pudo identificar tu perfil de médico."
        )
        return ConversationHandler.END
    history_id = ud.get('current_history_id')

    # 1. Construimos el diccionario completo con TODOS los datos
    admin_data = {
        'consultation_type': ud.get('consultation_type'),
        'admin_physical_exam': ud.get('physical_exam_notes'),
        'admin_ultrasound': ud.get('ultrasound_notes'),
        'admin_diagnosis': ud.get('diagnosis_notes'),
        'admin_plan': ud.get('plan_notes'),
        'admin_observations': ud.get('observation_notes') # Nuevo campo
    }

    # 2. Llamamos a la función de la base de datos para actualizar el registro
    success = await preconsulta_db.complete_history(history_id, doctor_id, admin_data)

    # 3. Mostramos el resultado y los botones finales
    if success:
        final_text = "✅ ¡Informe médico completado y guardado con éxito!"
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📄 Generar Informe (PDF)", callback_data=f"generate_pdf_{history_id}")],
            [InlineKeyboardButton("🔙 ", callback_data="list_histories_0")]
        ])
    else:
        final_text = "❌ Hubo un error al guardar el informe. Por favor, inténtalo de nuevo."
        reply_markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙", callback_data="list_histories_0")
        ]])

    # 4. Editamos el mensaje "ancla" por última vez
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=ud['consultation_anchor_message_id'],
        text=final_text,
        reply_markup=reply_markup
    )

    # 5. Limpiamos los datos y terminamos la conversación
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_consultation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela la creación del informe por parte del admin."""

    text = "Creación de informe cancelada."

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text)
    elif update.message:
        await update.message.reply_text(text)

    context.user_data.clear()
    return ConversationHandler.END

# features/preconsultas_admin/admin_handlers.py

@admin_required
async def view_history_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Muestra los detalles completos de una preconsulta, utilizando los resúmenes generados.
    """
    query = update.callback_query
    await query.answer()

    parts = query.data.split('_')
    try:
        history_id = int(parts[2])
    except (ValueError, IndexError):
        await query.edit_message_text("❌ Error: ID de historia no válido.")
        return

    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await query.edit_message_text("❌ Error: No se pudo identificar tu perfil de médico.")
        return
    details = await preconsulta_db.get_history_details(history_id, doctor_id)

    if not details:
        await query.edit_message_text("❌ Error: No se pudo encontrar la historia médica.")
        return

    # --- INICIO DE LA LÓGICA DE CONSTRUCCIÓN DEL TEXTO (REFACTORIZADA) ---

    history_number = details.get('history_number')
    text = f"📄 **Detalles de la Preconsulta #{details['id']}"
    if history_number:
        text += f" (NHM: {escape_html(history_number)})"
    text += "**\n\n"

    from datetime import datetime

    created_at = details.get('created_at')
    if isinstance(created_at, datetime):
        created_at_str = created_at.strftime('%Y-%m-%d')
    elif isinstance(created_at, str):
        created_at_str = created_at.split(' ')[0]
    else:
        created_at_str = '-'

    text += f"🗓️ **Fecha:** {created_at_str}\n"
    text += f"👤 **Paciente:** {escape_html(details.get('full_name', 'N/A'))}\n"
    text += f"🎯 **Tipo de Consulta:** {escape_html(details.get('consultation_type', 'N/A'))}\n"
    text += f"📌 **Motivo de Consulta:** {escape_html(details.get('reason_for_visit', 'N/A'))}\n\n"

    # -- SECCIÓN: INFORMACIÓN PERSONAL (sin cambios) --
    text += "--- **Información Personal** ---\n"
    personal_info = {
        "Edad": details.get('age'), "C.I.": details.get('ci'),
        "Teléfono": details.get('phone'), "Ocupación": details.get('occupation'),
        "Dirección": details.get('address')
    }
    text += "\n".join([f"<b>{k}:</b> {escape_html(str(v))}" for k, v in personal_info.items() if v])
    text += "\n\n"

    # -- SECCIÓN: ANTECEDENTES MÉDICOS (sin cambios) --
    text += "--- **Antecedentes Médicos** ---\n"
    medical_history = {
        "Madre": details.get('family_history_mother'),
        "Padre": details.get('family_history_father'),
        "Personales": details.get('personal_history'),
        "Suplementos": details.get('supplements'),
        "Quirúrgicos": details.get('surgical_history')
    }
    text += "\n".join([f"<b>{k}:</b> {escape_html(str(v))}" for k, v in medical_history.items() if v])
    text += "\n\n"

    # -- SECCIONES REFACTORIZADAS PARA USAR RESÚMENES --

    # Resumen Gineco-Obstétrico
    summary_gyn = details.get('summary_gyn_obstetric')
    if summary_gyn:
        text += f"--- **Antecedentes Gineco-Obstétricos** ---\n{escape_html(summary_gyn)}\n\n"

    # Resumen de Examen Funcional
    summary_func = details.get('summary_functional_exam')
    if summary_func:
        text += f"--- **Examen Funcional** ---\n{escape_html(summary_func)}\n\n"

    # Resumen de Hábitos
    summary_habits = details.get('summary_habits')
    if summary_habits:
        text += f"--- **Hábitos de Estilo de Vida** ---\n{escape_html(summary_habits)}\n\n"


    # --- INICIO DE LA MODIFICACIÓN CLAVE ---
    report_status = details.get('status', 'pending')

    # Si el informe ya fue completado por el médico, añadimos su evaluación.
    if report_status == 'completed':
        text += "--- **Evaluación Médica** ---\n"
        admin_fields = {
            "Examen Físico": details.get('admin_physical_exam'),
            "Ultrasonido Transvaginal": details.get('admin_ultrasound'),
            "Diagnóstico": details.get('admin_diagnosis'),
            "Plan": details.get('admin_plan'),
            "Observaciones": details.get('admin_observations')
        }
        # Añadimos solo los campos que tienen contenido
        admin_section_text = "\n".join([f"<b>{k}:</b> {escape_html(str(v))}" for k, v in admin_fields.items() if v])
        if admin_section_text:
            text += admin_section_text + "\n\n"



    # 4. Lógica para determinar a dónde debe llevar el botón "Volver"
    back_callback = "list_histories_0"
    back_text = "🔙 "

    try:
        source = parts[3]
        param = parts[4] if len(parts) > 4 else '0' # Usar '0' como página por defecto

        if source == 'patientarchive':
            user_id = details.get('user_id')
            if user_id:
                back_callback = f"view_patient_history_{user_id}"
                back_text = "🔙 "
            else:
                back_callback = "patient_archive_hub"
                back_text = "🔙 "

        elif source == 'pendinglist':
            back_callback = f"list_histories_{param}"
            # El texto "Volver a Pendientes" ya es el por defecto, no hace falta cambiarlo.

        elif source == 'patienthistory':
            user_id = param
            back_callback = f"patient_history_{user_id}"
            back_text = "🔙 "

    except IndexError:
        # Si el callback_data es simple (ej. 'view_history_123'),
        # los valores por defecto ('list_histories_0' y 'Volver a Pendientes') se usarán,
        # lo cual es el comportamiento correcto para este flujo.
        pass

    # 5. Lógica para determinar qué botones de acción mostrar
    report_status = details.get('status', 'pending')

    # 6. Construimos el teclado final
    reply_markup = keyboards.get_history_details_keyboard(
        history_id=history_id,
        status=report_status,
        back_callback=back_callback,
        back_text=back_text
    )

    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

def register(app: Application):
    """Registra los handlers para la gestión de preconsultas."""

    # --- Definición de la Conversación para Completar el Informe ---
    consultation_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_consultation, pattern='^start_consultation_')],
        states={
            AWAITING_EXAM_TEMPLATE_CHOICE: [
                CallbackQueryHandler(handle_exam_template_choice, pattern='^exam_choice_')
            ],
            AWAITING_EXAM_INPUT: [
                CallbackQueryHandler(process_exam_input, pattern=r'^ASK_'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_exam_input),
            ],
            AWAITING_PHYSICAL_EXAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, transition_to_ultrasound)],
            AWAITING_ULTRASOUND: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_ultrasound)],

            # Flujo de Diagnóstico (Múltiples ítems)
            AWAITING_DIAGNOSIS: [
                CallbackQueryHandler(add_another_diagnosis, pattern='^add_another_diagnóstico$'),
                CallbackQueryHandler(start_plan_step, pattern='^finish_diagnóstico$')
            ],
            ADDING_DIAGNOSIS_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_diagnosis_item)],

            # Flujo del Plan (Múltiples ítems)
            AWAITING_PLAN: [
                CallbackQueryHandler(add_another_plan_item, pattern='^add_another_plan$'),
                CallbackQueryHandler(ask_for_observations, pattern='^finish_plan$')
            ],
            ADDING_PLAN_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_plan_item)],

            # Estado final para recibir las observaciones.
            AWAITING_OBSERVATIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_observations_and_finish)],
        },
        fallbacks=[
            CommandHandler('cancelar', cancel_consultation),
            CallbackQueryHandler(cancel_consultation, pattern='^cancel_consultation_conv$')
        ],
        name="consultation_report_conversation",
        allow_reentry=True,
        persistent=True
    )

    # --- Registro de Handlers (Orden Corregido) ---

    # 1. Se registran PRIMERO las conversaciones
    app.add_handler(consultation_conv)

    # 2. Handlers básicos
    app.add_handler(CallbackQueryHandler(patient_management_hub, pattern=r'^patient_management_hub$'))
    app.add_handler(CallbackQueryHandler(list_medical_histories, pattern=r'^list_histories_\d+$'))
    app.add_handler(CallbackQueryHandler(view_history_details, pattern=r'^view_history_'))
    app.add_handler(CallbackQueryHandler(descartar_pdf_handler, pattern="^descartar_pdf_"))
    app.add_handler(CallbackQueryHandler(confirm_delete_history, pattern=r'^confirm_delete_history_'))
    app.add_handler(CallbackQueryHandler(execute_delete_history, pattern=r'^execute_delete_history_'))
    app.add_handler(CallbackQueryHandler(dismiss_preconsulta_notification, pattern=r'^preconsulta_dismiss_\d+$'))

    # 3. Handlers de PDF con patrones específicos (sin duplicados)
    app.add_handler(CallbackQueryHandler(generate_pdf_hub, pattern=r'^generate_pdf_\d+'))

    app.add_handler(CallbackQueryHandler(generate_summary_pdf_hub, pattern=r'^generate_summary_pdf_'))

    # Patrones flexibles que permiten sufijos opcionales (_patientarchive, _pendinglist_X, etc.)
    app.add_handler(CallbackQueryHandler(download_pdf, pattern=r'^download_pdf_\d+'))
    app.add_handler(CallbackQueryHandler(send_pdf_to_patient, pattern=r'^send_to_patient_\d+'))
    
    # 4. Handlers de PDF resumido (Informe Médico Resumido)
    from . import pdf_handlers
    pdf_handlers.register(app)
    #app.add_handler(CallbackQueryHandler(start_editing, pattern='^start_editing_'))
    # NOTA: Los handlers de edición (start_editing, etc.) deben estar registrados aquí si existen
    # Si tienes handlers para modificar informes, asegúrate de que estén registrados