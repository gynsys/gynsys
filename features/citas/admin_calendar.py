# features/citas/admin_calendar.py
import calendar
from datetime import date
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class CustomCalendar:
    def __init__(self):
        self.min_date = date.today()
        self.months_es = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        self.days_es = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"]

    def _generate_month(self, year: int, month: int, highlight_date: date = None, callback_prefix: str = "book_cal"):
        cal = calendar.monthcalendar(year, month); keyboard = []
        month_name = self.months_es[month-1]; keyboard.append([InlineKeyboardButton(f"« {month_name} {year} »", callback_data="ignore_display")])
        keyboard.append([InlineKeyboardButton(day, callback_data="ignore_header") for day in self.days_es])
        for week in cal:
            row = [];
            for day in week:
                if day == 0: row.append(InlineKeyboardButton(" ", callback_data="ignore_empty"))
                else:
                    current_date = date(year, month, day)
                    # La lógica para deshabilitar días pasados es correcta
                    if current_date < self.min_date and current_date != highlight_date: row.append(InlineKeyboardButton(" ", callback_data="ignore_empty"))
                    else:
                        style = "🗓️" if highlight_date and current_date == highlight_date else ""
                        btn_text = f"{style}{day}" if style else f"{day}"
                        # Usamos el prefijo que se pasa como parámetro
                        row.append(InlineKeyboardButton(btn_text, callback_data=f"{callback_prefix}_day_{current_date.isoformat()}"))
            keyboard.append(row)
        return keyboard

    # --- ¡CAMBIO AQUÍ! ---
    def _generate_year_navigation(self, year: int, month: int, callback_prefix: str):
        """
        Genera los botones de navegación de mes, AHORA SIN el botón 'Hoy'.
        """
        prev_month = month - 1 if month > 1 else 12; prev_year = year if month > 1 else year - 1
        next_month = month + 1 if month < 12 else 1; next_year = year if month < 12 else year + 1
        
        # Simplemente eliminamos el botón "Hoy" de la lista
        return [
            InlineKeyboardButton("◀️ Mes Ant.", callback_data=f"{callback_prefix}_nav_{prev_year}-{prev_month:02d}"),
            InlineKeyboardButton("Mes Sig. ▶️", callback_data=f"{callback_prefix}_nav_{next_year}-{next_month:02d}")
        ]

    # --- (El resto de la clase se queda como estaba) ---
    def create_booking_calendar(self, year: int = None, month: int = None):
        if year is None or month is None:
            today = date.today()
            year, month = today.year, today.month
        keyboard = self._generate_month(year, month, callback_prefix="book_cal")
        keyboard.append(self._generate_year_navigation(year, month, "book_cal"))
        keyboard.append([InlineKeyboardButton("❌ Cancelar Agendamiento", callback_data="book_cancel")])
        return InlineKeyboardMarkup(keyboard)

    def create_reschedule_calendar(self, cita_id: int, filter_type: str, page_index: int, year: int = None, month: int = None, highlight_date: date = None):
        if year is None or month is None:
            today = date.today()
            year, month = today.year, today.month

        # Generamos el mes usando el prefijo "resched_cal" explícitamente
        keyboard = self._generate_month(year, month, highlight_date, callback_prefix="resched_cal")
        
        # La navegación también usa la función modificada sin el botón "Hoy"
        keyboard.append(self._generate_year_navigation(year, month, "resched_cal"))
        
        keyboard.append([
            InlineKeyboardButton("🔄 Mantener Fecha", callback_data=f"resched_cal_keep_date"),
            InlineKeyboardButton("❌ Cancelar", callback_data=f"resched_cal_cancel")
        ])
        return InlineKeyboardMarkup(keyboard)

    def process_selection(self, query_data: str):
        if query_data.startswith("book_cal_day_") or query_data.startswith("resched_cal_day_"):
            return date.fromisoformat(query_data.split('_')[-1])
        return None