# features/preconsulta/calendar.py
import calendar
from datetime import date
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class FUMCalendar:
    def __init__(self):
        self.months_es = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        self.days_es = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"]

    def _generate_month(self, year: int, month: int):
        cal = calendar.monthcalendar(year, month)
        keyboard = []

        month_name = self.months_es[month-1]
        keyboard.append([InlineKeyboardButton(f"{month_name} {year}", callback_data="ignore")])
        keyboard.append([InlineKeyboardButton(day, callback_data="ignore") for day in self.days_es])

        today = date.today()
        for week in cal:
            row = []
            for day in week:
                if day == 0:
                    row.append(InlineKeyboardButton(" ", callback_data="ignore"))
                else:
                    current_date = date(year, month, day)
                    btn_text = f"❗{day}" if current_date == today else str(day)
                    row.append(InlineKeyboardButton(btn_text, callback_data=f"fum_cal_day_{current_date.isoformat()}"))
            keyboard.append(row)
        return keyboard

    def _generate_navigation(self, year: int, month: int):
        prev_month_date = f"{(date(year, month, 1) - date.resolution).year}-{(date(year, month, 1) - date.resolution).month:02d}"
        next_month_date = f"{(date(year, month, 1) + date.resolution * 31).year}-{(date(year, month, 1) + date.resolution * 31).month:02d}"

        return [
            InlineKeyboardButton("◀️ Mes", callback_data=f"fum_cal_nav_{prev_month_date}"),
            InlineKeyboardButton("Hoy", callback_data=f"fum_cal_nav_{date.today().year}-{date.today().month:02d}"),
            InlineKeyboardButton("Mes ▶️", callback_data=f"fum_cal_nav_{next_month_date}")
        ]

    def _generate_year_selection(self, year: int, month: int):
        return [
            InlineKeyboardButton("⏪ Año", callback_data=f"fum_cal_nav_{year-1}-{month:02d}"),
            InlineKeyboardButton(f"Año {year}", callback_data="ignore"),
            InlineKeyboardButton("Año ⏩", callback_data=f"fum_cal_nav_{year+1}-{month:02d}")
        ]

    def create_calendar(self, year: int = None, month: int = None):
        if year is None or month is None:
            today = date.today()
            year, month = today.year, today.month

        keyboard = self._generate_month(year, month)
        # --- ¡NUEVAS FILAS AQUÍ! ---
        keyboard.append(self._generate_navigation(year, month))
        keyboard.append(self._generate_year_selection(year, month))

        #keyboard.append([InlineKeyboardButton("❌ Cancelar Selección", callback_data="cancel_conv")])

        return InlineKeyboardMarkup(keyboard)

    def process_selection(self, query_data: str):
        if query_data.startswith("fum_cal_day_"):
            return date.fromisoformat(query_data.split('_')[-1])
        return None