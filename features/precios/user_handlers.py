# /features/precios/user_handlers.py
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest
from database import content_db
from common import texts
from common.keyboards import get_back_to_menu_keyboard
from common.context_manager import get_tenant_id
from .keyboards import get_precios_keyboard
from utils.role_manager import RoleManager
from config import DB_PATH

role_manager = RoleManager(DB_PATH)

async def show_precios_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    bot_id = await get_tenant_id(update, context)
    if not bot_id:
        await query.answer("❌ Error al obtener información.", show_alert=True)
        return

    texto = await texts.get_texto('header_precios', bot_id, '💰 Inversión en tu Salud')
    reply_markup = await get_precios_keyboard(bot_id)

    # Manejar transición desde mensaje con imagen
    try:
        await query.edit_message_text(text=texto, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except BadRequest as e:
        if "no text" in str(e).lower() or "message to edit not found" in str(e).lower():
            try:
                await query.message.delete()
            except:
                pass
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=texto,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )

async def show_precio_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    item_id = int(query.data.split('_')[-1])
    texto = await content_db.get_item_content(item_id, 'content', table_name='precios')

    if not texto:
        texto = "❌ Contenido no encontrado."

    # --- INICIO DE LA LÓGICA INTELIGENTE PARA EL BOTÓN "VOLVER" ---

    user_id = update.effective_user.id
    user_role = await role_manager.get_user_role(user_id)

    # Definimos el callback de retorno por defecto para el caso más genérico (ej. SuperAdmin)
    back_callback = 'precios_menu'

    # Asignamos el callback correcto según el rol del usuario
    if user_role == 'doctor':
        # El botón "Precios" del menú del doctor tiene el callback 'doctor_pricing'
        back_callback = 'doctor_pricing'
    elif user_role == 'patient':
        # El botón "Precios" del menú del paciente tiene el callback 'patient_pricing'
        back_callback = 'patient_pricing'

    # Para cualquier otro rol (como 'superadmin' o 'new_user'), se usará el 'precios_menu' por defecto,
    # que es el correcto para el panel de admin del SuperAdmin.

    # --- FIN DE LA LÓGICA INTELIGENTE ---

    try:
        await query.edit_message_text(
            text=texto,
            reply_markup=get_back_to_menu_keyboard(back_callback),
            parse_mode=ParseMode.HTML
        )
    except BadRequest as e:
        # Manejo de error por si el mensaje original no se puede editar
        if "no text" in str(e).lower() or "message to edit not found" in str(e).lower():
            try:
                await query.message.delete()
            except:
                pass
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=texto,
                reply_markup=get_back_to_menu_keyboard(back_callback),
                parse_mode=ParseMode.HTML
            )
'''
async def show_precio_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    item_id = int(query.data.split('_')[-1])
    texto = await content_db.get_item_content(item_id, 'content', table_name='precios')
    user_id = update.effective_user.id
    user_role = await role_manager.get_user_role(user_id)

    back_callback = 'main_menu' # Valor por defecto seguro

    if user_role == 'doctor':
        # El callback que lleva al médico a su lista de precios es 'doctor_pricing'
        back_callback = 'doctor_pricing'
    elif user_role == 'patient':
        # El callback que lleva al paciente a su lista de precios es 'patient_pricing'
        back_callback = 'patient_pricing'
    if not texto:
        texto = "❌ Contenido no encontrado."

    # Obtener bot_id para el callback de volver
    bot_id = await get_tenant_id(update, context)
    #back_callback = 'precios_menu' if bot_id else 'main_menu'
    back_callback = 'patient_pricing' if bot_id else 'main_menu

    try:
        await query.edit_message_text(
            text=texto,
            reply_markup=get_back_to_menu_keyboard(back_callback),
            parse_mode=ParseMode.HTML
        )
    except BadRequest as e:
        if "no text" in str(e).lower() or "message to edit not found" in str(e).lower():
            try:
                await query.message.delete()
            except:
                pass
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=texto,
                reply_markup=get_back_to_menu_keyboard(back_callback),
                parse_mode=ParseMode.HTML
            )

def register(app: Application):
    app.add_handler(CallbackQueryHandler(show_precios_menu, pattern='^precios$'))
    app.add_handler(CallbackQueryHandler(show_precio_content, pattern='^precio_item_'))'''

def register(app: Application):
    """Registra los handlers para el módulo de precios, cubriendo todos los roles."""

    # 1. Handler para la vista de lista de precios.
    #    Responde a los diferentes callbacks de cada rol, pero todos ejecutan la misma función.
    app.add_handler(CallbackQueryHandler(show_precios_menu, pattern='^precios_menu$'))   # Para el SuperAdmin
    app.add_handler(CallbackQueryHandler(show_precios_menu, pattern='^doctor_pricing$'))  # Para el Doctor/Inquilino
    app.add_handler(CallbackQueryHandler(show_precios_menu, pattern='^patient_pricing$')) # Para el Paciente

    # 2. Handler para la vista de detalle de un precio.
    #    Se activa cuando un usuario hace clic en un ítem de la lista.
    app.add_handler(CallbackQueryHandler(show_precio_content, pattern='^precio_item_'))