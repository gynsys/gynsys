# features/preconsulta/main_handler.py

import logging
from telegram import Update # <-- Añade esto
from telegram.error import BadRequest
from telegram.ext import Application, ConversationHandler, CallbackQueryHandler, MessageHandler, filters, CommandHandler, ContextTypes
from .states import AWAITING_GENERIC_INPUT, AWAITING_CHECKLIST_OTHER


from .patient_flow.generic_flow_engine import start_preconsultation_flow, process_input, render_node, preconsultation_flow
from common import texts
# En el bot nuevo, el comando /start será manejado por el handler principal de main.py
# No necesitamos un fallback aquí, el ConversationHandler simplemente terminará
async def start_command_handler(update, context):
    """Fallback simple que termina la conversación"""
    return ConversationHandler.END
from .patient_flow.flow_actions.checklist import process_other_input

from common.decorators import admin_required

logger = logging.getLogger(__name__)

@admin_required
async def debug_flow_jump(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Comando de admin para saltar a un nodo específico del flujo de preconsulta
    con datos de prueba. Uso: /debug_flow NOMBRE_DEL_NODO
    """
    if not context.args:
        await update.message.reply_text("Uso: /debug_flow <NOMBRE_DEL_NODO>")
        return

    node_id_to_jump = context.args[0]

    # Verificamos si el nodo existe en el flujo
    if node_id_to_jump not in preconsultation_flow['nodes']:
        await update.message.reply_text(f"❌ Nodo '{node_id_to_jump}' no encontrado en el flujo.")
        return

    # Limpiamos y preparamos el contexto
    context.user_data.clear()
    context.user_data['flow'] = preconsultation_flow

    # Poblamos con datos de prueba
    context.user_data.update({
        'full_name': 'Usuario de Prueba',
        'age': '30',
        'consultation_type': 'Ginecológica',
        'reason_for_visit': 'Test de Resumen',
        'functional_dispareunia': 'Sí, de tipo Profunda (Intensidad: 8/10)',
        'functional_leg_pain': 'Sí (Tipo: Corriente, Zona: Zona de glúteos)',
        'functional_gastro_before': 'Dolor al evacuar',
        'functional_gastro_during': 'Distensión abdominal, Dolor al evacuar',
        'functional_dischezia': 'Eventual',
        'functional_bowel_freq': 'Cada 3 días',
        'functional_urinary_problem': 'Sí',
        'functional_urinary_pain': 'Sí (Intensidad: 9/10)',
        'functional_urinary_irritation': 'Sí',
        'functional_urinary_incontinence': 'No',
        'functional_urinary_nocturia': 'Sí'
    })

    await update.message.reply_text(f"🚀 Saltando al nodo de depuración: {node_id_to_jump}...")

    # Creamos un mensaje ancla para que el motor lo use
    anchor_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Iniciando depuración..."
    )
    context.user_data['anchor_message_id'] = anchor_message.message_id

    # Llamamos al renderizador del motor para iniciar el flujo desde el punto deseado
    return await render_node(update, context, node_id_to_jump)

async def process_input_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("\n>>> CONV_HANDLER llama a process_input...")
    result = await process_input(update, context)
    print(f"<<< process_input devolvió: {result} (Tipo: {type(result)})")
    return result

async def process_other_input_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("\n>>> CONV_HANDLER llama a process_other_input...")
    result = await process_other_input(update, context)
    print(f"<<< process_other_input devolvió: {result} (Tipo: {type(result)})")
    return result

async def start_preconsultation_flow_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("\n>>> CONV_HANDLER llama a start_preconsultation_flow (entry_point)...")
    result = await start_preconsultation_flow(update, context)
    print(f"<<< start_preconsultation_flow devolvió: {result} (Tipo: {type(result)})")
    return result

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela la preconsulta en cualquier punto, manejando comandos y callbacks."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    query = update.callback_query

    if query:
        await query.answer()

    cancel_text = texts.get_text('preconsulta.cancel_message', "Preconsulta cancelada.")
    anchor_id = context.user_data.get('anchor_message_id')

    # --- INICIO DE LA LÓGICA CORREGIDA ---

    try:
        # CASO 1: El usuario pulsó un botón de cancelación. Editamos ese mensaje.
        if query and query.message:
            await query.edit_message_text(text=cancel_text)

        # CASO 2: El usuario escribió /cancelar y tenemos un mensaje ancla para editar.
        elif anchor_id:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=anchor_id,
                text=cancel_text,
                # Quitamos cualquier teclado que pudiera tener
                reply_markup=None
            )
            # Borramos el mensaje /cancelar para mantener el chat limpio
            if update.message:
                await update.message.delete()

        # CASO 3: Fallback por si no podemos editar (ej. el ancla no existe).
        else:
            if update.message:
                await update.message.reply_text(cancel_text)
            else:
                await context.bot.send_message(chat_id=chat_id, text=cancel_text)

    except BadRequest as e:
        # Si editar falla (ej. el mensaje no existe), enviamos uno nuevo como fallback.
        logger.warning(f"No se pudo editar el mensaje de cancelación para el usuario {user_id}: {e}")
        await context.bot.send_message(chat_id=chat_id, text=cancel_text)

    # --- FIN DE LA LÓGICA CORREGIDA ---

    context.user_data.clear()
    return ConversationHandler.END


def register(app: Application):
    """Registra el ConversationHandler completo de la preconsulta."""

    states_map = {
        AWAITING_GENERIC_INPUT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_input),
            CallbackQueryHandler(process_input)
        ],
        AWAITING_CHECKLIST_OTHER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_other_input)
        ]
    }
    logger.info(f"Registrando ConversationHandler con {len(states_map)} estados. Estados conocidos: {sorted(states_map.keys())}")

    preconsultation_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_preconsultation_flow, pattern='^preconsulta_start_')],
        states=states_map,
        fallbacks=[
            CommandHandler('cancelar', cancel),
            CommandHandler('start', start_command_handler),
            CallbackQueryHandler(cancel, pattern='^cancel_conv$')
        ]
    )
    app.add_handler(CommandHandler("debug_flow", debug_flow_jump))
    app.add_handler(preconsultation_conv)