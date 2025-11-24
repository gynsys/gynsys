#!/usr/bin/env python3
"""
Script para debuggear el flujo obstétrico (HO).
Verifica qué valores se están recibiendo y por qué no se cumple la condición.
"""
import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_PATH
from database.session import get_session
from database.repositories.appointment_repository import AppointmentRepository
from database.models.appointment import Appointment
from sqlalchemy import select, desc
import aiosqlite

async def debug_obstetric_flow(user_id: int = None, appointment_id: int = None):
    """
    Debuggea el flujo obstétrico para una cita específica o la última del usuario.
    """
    print("=" * 70)
    print("🔍 DEBUG: Flujo Obstétrico (HO)")
    print("=" * 70)
    
    async with get_session() as session:
        appointment_repo = AppointmentRepository(session)
        
        # Obtener la cita
        if appointment_id:
            print(f"\n📋 Buscando cita ID: {appointment_id}")
            appointment_data = await appointment_repo.get_appointment_by_id(appointment_id, None)
        elif user_id:
            print(f"\n📋 Buscando última cita del usuario: {user_id}")
            # Buscar la última cita del usuario
            stmt = (
                select(Appointment)
                .where(Appointment.patient_telegram_id == user_id)
                .order_by(desc(Appointment.id))
                .limit(1)
            )
            result = await session.execute(stmt)
            appointment = result.scalar_one_or_none()
            
            if appointment:
                # Obtener datos completos de la cita
                appointment_data = await appointment_repo.get_appointment_by_id(appointment.id, None)
            else:
                print("❌ No se encontró ninguna cita para este usuario.")
                return
        else:
            print("❌ Debes proporcionar user_id o appointment_id")
            return
        
        if not appointment_data:
            print("❌ No se encontró la cita.")
            return
        
        # Convertir a dict si es necesario
        if hasattr(appointment_data, 'keys'):
            appointment_dict = dict(appointment_data)
        else:
            appointment_dict = appointment_data
        
        print("\n" + "=" * 70)
        print("📊 DATOS DE LA CITA:")
        print("=" * 70)
        
        # Mostrar todos los campos de la cita
        for key, value in appointment_dict.items():
            print(f"  {key}: {value} (tipo: {type(value).__name__})")
        
        # Extraer los valores relevantes
        consultation_type = appointment_dict.get('consultation_type')
        is_first_pregnancy = appointment_dict.get('is_first_pregnancy')
        has_been_pregnant = appointment_dict.get('has_been_pregnant')
        
        print("\n" + "=" * 70)
        print("🎯 VALORES RELEVANTES PARA DECIDE_OBSTETRIC_FLOW:")
        print("=" * 70)
        print(f"  consultation_type: {consultation_type} (tipo: {type(consultation_type).__name__})")
        print(f"  is_first_pregnancy: {is_first_pregnancy} (tipo: {type(is_first_pregnancy).__name__})")
        print(f"  has_been_pregnant: {has_been_pregnant} (tipo: {type(has_been_pregnant).__name__})")
        
        # Verificar valores None/Null
        print("\n" + "=" * 70)
        print("⚠️  VERIFICACIÓN DE VALORES:")
        print("=" * 70)
        if consultation_type is None:
            print("  ❌ consultation_type es None/Null")
        else:
            print(f"  ✅ consultation_type = '{consultation_type}'")
        
        if is_first_pregnancy is None:
            print("  ⚠️  is_first_pregnancy es None/Null")
        else:
            print(f"  ✅ is_first_pregnancy = {is_first_pregnancy}")
        
        if has_been_pregnant is None:
            print("  ⚠️  has_been_pregnant es None/Null")
        else:
            print(f"  ✅ has_been_pregnant = {has_been_pregnant}")
        
        # Simular la lógica de decide_obstetric_flow
        print("\n" + "=" * 70)
        print("🧪 SIMULACIÓN DE DECIDE_OBSTETRIC_FLOW:")
        print("=" * 70)
        
        # CASO 1: Prenatal + Sin embarazos previos -> PRIMIGESTA
        if consultation_type == 'Prenatal' and is_first_pregnancy is True:
            print("  ✅ CASO 1: Prenatal-Primigesta. Saltando bucle HO.")
            print("     → Debería retornar: node['next_if_skip']")
        # CASO 2: Prenatal + Con embarazos previos -> NECESITA HO
        elif consultation_type == 'Prenatal' and is_first_pregnancy is False:
            print("  ✅ CASO 2: Prenatal-Multigesta. Entrando a bucle HO.")
            print("     → Debería retornar: node['next_if_needed']")
        # CASO 3: Ginecológica + Sin embarazos previos -> NULIGESTA
        elif consultation_type == 'Ginecológica' and has_been_pregnant is False:
            print("  ✅ CASO 3: Ginecológica-Nuligesta. Saltando bucle HO.")
            print("     → Debería retornar: node['next_if_skip']")
        # CASO 4: Ginecológica + Con embarazos previos -> NECESITA HO
        elif consultation_type == 'Ginecológica' and has_been_pregnant is True:
            print("  ✅ CASO 4: Ginecológica con historial. Entrando a bucle HO.")
            print("     → Debería retornar: node['next_if_needed']")
        else:
            print("  ❌ FALLBACK: No se pudo determinar el flujo obstétrico")
            print("     → Esto significa que alguna condición no se cumplió")
            print("\n  🔍 Análisis detallado:")
            
            if consultation_type != 'Ginecológica' and consultation_type != 'Prenatal':
                print(f"     - consultation_type '{consultation_type}' no es 'Ginecológica' ni 'Prenatal'")
            
            if consultation_type == 'Ginecológica':
                print("     - consultation_type es 'Ginecológica' ✓")
                if has_been_pregnant is None:
                    print("     - has_been_pregnant es None (debería ser False o True)")
                elif has_been_pregnant is not False:
                    print(f"     - has_been_pregnant es {has_been_pregnant} (debería ser False para CASO 3)")
            
            if consultation_type == 'Prenatal':
                print("     - consultation_type es 'Prenatal' ✓")
                if is_first_pregnancy is None:
                    print("     - is_first_pregnancy es None (debería ser True o False)")
                elif is_first_pregnancy is not True:
                    print(f"     - is_first_pregnancy es {is_first_pregnancy} (debería ser True para CASO 1)")
        
        print("\n" + "=" * 70)
        print("💡 RECOMENDACIONES:")
        print("=" * 70)
        
        if consultation_type == 'Ginecológica' and has_been_pregnant is None:
            print("  ⚠️  has_been_pregnant es None. Debería ser False para CASO 3.")
            print("     Verifica cómo se guarda este valor en confirm_appointment()")
        elif consultation_type == 'Ginecológica' and has_been_pregnant is not False:
            print(f"  ⚠️  has_been_pregnant es {has_been_pregnant}, debería ser False para CASO 3.")
            print("     Verifica la lógica en handle_ever_pregnant() o handle_pregnancy_info()")
        
        print("\n" + "=" * 70)

async def list_user_appointments(user_id: int):
    """Lista todas las citas de un usuario."""
    async with get_session() as session:
        stmt = (
            select(Appointment)
            .where(Appointment.patient_telegram_id == user_id)
            .order_by(desc(Appointment.id))
            .limit(10)
        )
        result = await session.execute(stmt)
        appointments = result.scalars().all()
        
        print(f"\n📋 Últimas 10 citas del usuario {user_id}:")
        print("=" * 70)
        for appt in appointments:
            print(f"\n  Cita ID: {appt.id}")
            print(f"  - consultation_type: {appt.consultation_type}")
            print(f"  - is_first_pregnancy: {appt.is_first_pregnancy}")
            print(f"  - has_been_pregnant: {appt.has_been_pregnant}")
            print(f"  - Fecha creación: {appt.created_at}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python scripts/debug_obstetric_flow.py <user_id>")
        print("  python scripts/debug_obstetric_flow.py <user_id> <appointment_id>")
        print("\nEjemplo:")
        print("  python scripts/debug_obstetric_flow.py 123456789")
        print("  python scripts/debug_obstetric_flow.py 123456789 42")
        sys.exit(1)
    
    user_id = int(sys.argv[1])
    appointment_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    # Primero listar las citas
    asyncio.run(list_user_appointments(user_id))
    
    # Luego debuggear
    asyncio.run(debug_obstetric_flow(user_id=user_id, appointment_id=appointment_id))

