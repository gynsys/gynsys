import math
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes
from database.session import get_session
from database.repositories.user_repository import DoctorRepository
from config import DB_PATH
from utils.logger import get_logger, perm_logger


class DoctorsManagementHandler:
    def __init__(self):
        self.logger = get_logger("DoctorsManagement")
        self.doctors_per_page = 5
    
    def get_doctors_management_keyboard(self, doctors, page=0, total_pages=1):
        """Teclado para gestión de médicos con paginación"""
        keyboard = []
        
        # Agregar cada médico con botones de acción
        for doctor in doctors:
            doctor_id, name, telegram_id, is_active, created_at = doctor
            keyboard.append([
                InlineKeyboardButton("🗑️", callback_data=f"delete_doctor_{doctor_id}"),
                InlineKeyboardButton(f"👨‍⚕️ {name}", callback_data=f"info_doctor_{doctor_id}"),
                InlineKeyboardButton("🔒 Restringir", callback_data=f"restrict_doctor_{doctor_id}")
            ])
        
        # Botones de paginación
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"doctors_page_{page-1}"))
        
        pagination_buttons.append(InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="current_page"))
        
        if page < total_pages - 1:
            pagination_buttons.append(InlineKeyboardButton("Siguiente ➡️", callback_data=f"doctors_page_{page+1}"))
        
        if pagination_buttons:
            keyboard.append(pagination_buttons)
        
        # Botones de acción general
        keyboard.append([
            InlineKeyboardButton("🔄 Actualizar", callback_data="refresh_doctors"),
            InlineKeyboardButton("👨‍⚕️ Volver a Médicos", callback_data="doctors_menu")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    async def show_doctors_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE, page=0, show_inactive=False):
        """Muestra la gestión paginada de médicos"""
        query = update.callback_query
        await query.answer()

        try:
            # Obtener médicos según filtro
            async with get_session() as session:
                repo = DoctorRepository(session)
                if show_inactive:
                    active_doctors = await repo.get_all_doctors()
                    inactive_doctors = await repo.get_inactive_doctors()
                    all_doctors = [
                        (d.id, d.name, d.telegram_id, d.is_active, d.created_at)
                        for d in active_doctors + inactive_doctors
                    ]
                    list_type = "Todos los Médicos (Activos e Inactivos)"
                else:
                    doctors = await repo.get_all_doctors()
                    all_doctors = [
                        (d.id, d.name, d.telegram_id, d.is_active, d.created_at)
                        for d in doctors
                    ]
                    list_type = "Médicos Activos"

            total_doctors = len(all_doctors)
            total_pages = math.ceil(total_doctors / self.doctors_per_page) if total_doctors > 0 else 1

            # Validar página
            page = max(0, min(page, total_pages - 1))

            # Obtener slice de médicos para esta página
            start_idx = page * self.doctors_per_page
            end_idx = start_idx + self.doctors_per_page
            page_doctors = all_doctors[start_idx:end_idx]

            # Agregar timestamp único para evitar error "Message is not modified"
            from datetime import datetime
            timestamp = f"\n\n🕐 _Actualizado: {datetime.now().strftime('%H:%M:%S')}_"

            if not page_doctors:
                await query.edit_message_text(
                    f"📋 **Gestión de Médicos**\n\n"
                    f"{list_type}\n\n"
                    f"No hay médicos registrados en el sistema.{timestamp}",
                    reply_markup=self.get_doctors_management_keyboard([], page, total_pages, show_inactive),
                    parse_mode="Markdown"
                )
                return

            # Construir mensaje
            message = f"📋 **Gestión de Médicos**\n\n"
            message += f"**{list_type}**\n"
            message += f"📊 **Total:** {total_doctors}\n"
            message += f"📄 **Página:** {page + 1} de {total_pages}"
            message += timestamp + "\n\n"

            if show_inactive:
                message += "**Leyenda:**\n"
                message += "✅ - Médico activo\n"
                message += "❌ - Médico inactivo (eliminado/restringido)\n"
                message += "♻️ - Reactivar médico\n\n"

            message += "**Acciones por médico:**\n"
            message += "🗑️ - Eliminar médico (no paga suscripción)\n"
            message += "🔒 - Restringir acceso (morosidad)\n"

            if show_inactive:
                message += "♻️ - Reactivar médico\n\n"
            else:
                message += "\n"

            message += "**Médicos en esta página:**\n"

            for i, doctor in enumerate(page_doctors, start_idx + 1):
                doctor_id, name, telegram_id, is_active, created_at = doctor
                status_emoji = "✅" if is_active else "❌"
                status_text = "Activo" if is_active else "Inactivo"
                message += f"{i}. {status_emoji} {name} (ID: {telegram_id}) - {status_text}\n"

            # Usar try-except para manejar el error específico de "Message not modified"
            try:
                await query.edit_message_text(
                    message,
                    reply_markup=self.get_doctors_management_keyboard(page_doctors, page, total_pages, show_inactive),
                    parse_mode="Markdown"
                )
            except BadRequest as e:
                if "Message is not modified" in str(e):
                    # Si el mensaje es idéntico, solo responder con un feedback sutil
                    await query.answer("✅ La información ya está actualizada")
                else:
                    # Relanzar otros errores BadRequest
                    raise e

        except Exception as e:
            self.logger.error(f"Error mostrando gestión de médicos: {e}")

            # Mensaje de error con timestamp único también
            from datetime import datetime
            timestamp = f"\n\n🕐 _Error: {datetime.now().strftime('%H:%M:%S')}_"

            await query.edit_message_text(
                f"❌ **Error al cargar la gestión de médicos**{timestamp}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("👨‍⚕️ Volver a Médicos", callback_data="doctors_menu")
                ]])
            )
    async def handle_delete_doctor(self, update: Update, context: ContextTypes.DEFAULT_TYPE, doctor_id):
        """Elimina un médico (no paga suscripción)"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Obtener info del médico antes de eliminar
            async with get_session() as session:
                repo = DoctorRepository(session)
                doctor = await repo.get_doctor_by_id(doctor_id)
                if doctor:
                    doctor_name = doctor.name
                    # Eliminar médico
                    success = await repo.delete_doctor(doctor_id)
                    
                    if success:
                        self.logger.info(f"Médico eliminado: {doctor_name} (ID: {doctor_id})")
                        perm_logger.log_doctor_deleted(doctor_name, doctor_id, update.effective_user.id)
                        
                        await query.edit_message_text(
                            f"✅ **Médico Eliminado**\n\n"
                            f"👨‍⚕️ **Nombre:** {doctor_name}\n"
                            f"🆔 **ID:** {doctor_id}\n\n"
                            f"El médico ha sido eliminado del sistema por falta de pago de suscripción.",
                            parse_mode="Markdown"
                        )
                    else:
                        await query.edit_message_text(
                            "❌ **Error al eliminar médico**\n\n"
                            "No se pudo eliminar el médico. Intenta nuevamente.",
                            parse_mode="Markdown"
                        )
                else:
                    await query.edit_message_text(
                        "❌ **Médico no encontrado**\n\n"
                        "El médico que intentas eliminar no existe en el sistema.",
                        parse_mode="Markdown"
                    )
            
            # Esperar 2 segundos y volver a la gestión
            await asyncio.sleep(2)
            await self.show_doctors_management(update, context, page=0)
            
        except Exception as e:
            self.logger.error(f"Error eliminando médico: {e}")
            await query.edit_message_text(
                "❌ **Error al eliminar médico**",
                parse_mode="Markdown"
            )
    
    async def handle_restrict_doctor(self, update: Update, context: ContextTypes.DEFAULT_TYPE, doctor_id):
        """Restringe el acceso de un médico (morosidad)"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Obtener info del médico antes de restringir
            async with get_session() as session:
                repo = DoctorRepository(session)
                doctor = await repo.get_doctor_by_id(doctor_id)
                if doctor:
                    doctor_name = doctor.name
                    # Restringir médico
                    success = await repo.delete_doctor(doctor_id)
                    
                    if success:
                        self.logger.info(f"Médico restringido: {doctor_name} (ID: {doctor_id})")
                        perm_logger.log_doctor_restricted(doctor_name, doctor_id, update.effective_user.id)
                        
                        await query.edit_message_text(
                            f"🔒 **Acceso Restringido**\n\n"
                            f"👨‍⚕️ **Nombre:** {doctor_name}\n"
                            f"🆔 **ID:** {doctor_id}\n\n"
                            f"El médico ha sido restringido por morosidad. No podrá acceder al sistema.",
                            parse_mode="Markdown"
                        )
                    else:
                        await query.edit_message_text(
                            "❌ **Error al restringir médico**\n\n"
                            "No se pudo restringir el acceso del médico. Intenta nuevamente.",
                            parse_mode="Markdown"
                        )
                else:
                    await query.edit_message_text(
                        "❌ **Médico no encontrado**\n\n"
                        "El médico que intentas restringir no existe en el sistema.",
                        parse_mode="Markdown"
                    )
            
            # Esperar 2 segundos y volver a la gestión
            await asyncio.sleep(2)
            await self.show_doctors_management(update, context, page=0)
            
        except Exception as e:
            self.logger.error(f"Error restringiendo médico: {e}")
            await query.edit_message_text(
                "❌ **Error al restringir médico**",
                parse_mode="Markdown"
            )

# Instancia global
doctors_management = DoctorsManagementHandler()