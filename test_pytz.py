import datetime
import pytz

tz = pytz.timezone('America/Caracas')
t = datetime.time(hour=9, minute=30, tzinfo=tz)
print(f"Time constructed directly with tzinfo: {t}")
print(f"Time offset: {t.tzname()}")
