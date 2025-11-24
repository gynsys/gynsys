#!/usr/bin/env python3
"""
Script para listar las citas más recientes y encontrar la correcta.
"""
import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.session import get_session
from database.models.appointment import Appointment
from sqlalchemy import select, desc

async def list_recent_appointments(limit=20):
    """Lista las citas más recientes."""
    async with get_session() as session:
        stmt = (
            select(Appointment)
            .order_by(desc(Appointment.id))
            .limit(limit)
        )
        result = await session.execute(stmt)
        appointments = result.scalars().all()
        
        print(f"\n📋 Últimas {limit} citas en el sistema:")
        print("=" * 80)
        for appt in appointments:
            print(f"\n  Cita ID: {appt.id}")
            print(f"  - Usuario (Telegram ID): {appt.patient_telegram_id}")
            print(f"  - Nombre: {appt.patient_name}")
            print(f"  - Tipo Consulta: {appt.consultation_type}")
            # Verificar si los campos existen
            is_first = getattr(appt, 'is_first_pregnancy', 'NO EXISTE EN MODELO')
            has_been = getattr(appt, 'has_been_pregnant', 'NO EXISTE EN MODELO')
            print(f"  - is_first_pregnancy: {is_first}")
            print(f"  - has_been_pregnant: {has_been}")
            print(f"  - Estado: {appt.status}")
            print(f"  - Fecha creación: {appt.created_at if hasattr(appt, 'created_at') else 'N/A'}")
            print("-" * 80)

if __name__ == "__main__":
    asyncio.run(list_recent_appointments())

