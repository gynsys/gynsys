#!/usr/bin/env python3
"""
Script de prueba COMPLETO para el flujo obstétrico (HO).
Prueba el flujo completo: guardado → carga → decisión.
Simula la creación de citas y verifica que todo funcione correctamente.
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_PATH
from database.session import get_session
from database.repositories.appointment_repository import AppointmentRepository, SlotRepository
from database.models.appointment import Appointment, Slot
from features.preconsulta.flow_actions.services.formula_calculator import (
    get_primigesta_formula,
    get_nuligesta_formula
)
from sqlalchemy import select

# Simular la función decide_obstetric_flow
def simulate_decide_obstetric_flow(consultation_type, is_first_pregnancy, has_been_pregnant):
    """
    Simula la lógica de decide_obstetric_flow.
    Retorna: (caso, descripcion, deberia_entrar_ho, formula_ho)
    """
    # CASO 1: Prenatal + Sin embarazos previos -> PRIMIGESTA (SALTA HO)
    if consultation_type == 'Prenatal' and is_first_pregnancy is True:
        formula = get_primigesta_formula()
        return ("CASO 1", "Prenatal-Primigesta", False, formula)
    
    # CASO 2: Prenatal + Con embarazos previos -> NECESITA HO
    if consultation_type == 'Prenatal' and is_first_pregnancy is False:
        return ("CASO 2", "Prenatal-Multigesta", True, None)
    
    # CASO 3: Ginecológica + Sin embarazos previos -> NULIGESTA (SALTA HO)
    if consultation_type == 'Ginecológica' and has_been_pregnant is False:
        formula = get_nuligesta_formula()
        return ("CASO 3", "Ginecológica-Nuligesta", False, formula)
    
    # CASO 4: Ginecológica + Con embarazos previos -> NECESITA HO
    if consultation_type == 'Ginecológica' and has_been_pregnant is True:
        return ("CASO 4", "Ginecológica con historial", True, None)
    
    # FALLBACK: No se pudo determinar
    return ("FALLBACK", "No se pudo determinar", True, None)


async def test_complete_obstetric_flow():
    """
    Prueba el flujo completo: crear citas → guardar → cargar → verificar decisión.
    """
    print("=" * 80)
    print("🧪 PRUEBA COMPLETA: Flujo Obstétrico (HO) - Guardado → Carga → Decisión")
    print("=" * 80)
    
    # Casos de prueba: (nombre, consultation_type, is_first_pregnancy, has_been_pregnant)
    test_cases = [
        ("CASO 1: Prenatal-Primigesta", "Prenatal", True, None),
        ("CASO 2: Prenatal-Multigesta", "Prenatal", False, None),
        ("CASO 3: Ginecológica-Nuligesta", "Ginecológica", None, False),
        ("CASO 4: Ginecológica con historial", "Ginecológica", None, True),
    ]
    
    async with get_session() as session:
        slot_repo = SlotRepository(session)
        appointment_repo = AppointmentRepository(session)
        
        # Necesitamos un doctor_id de prueba (usar el primero disponible o crear uno de prueba)
        # Por ahora, usaremos doctor_id=1 como prueba
        doctor_id = 1
        test_user_id = 999999999  # ID de prueba que no debería existir
        
        print(f"\n📋 Configuración de prueba:")
        print(f"  - Doctor ID: {doctor_id}")
        print(f"  - Usuario de prueba ID: {test_user_id}")
        print(f"  - Total de casos a probar: {len(test_cases)}\n")
        
        resultados = []
        appointment_ids_creados = []
        
        for i, (nombre_caso, consultation_type, is_first_pregnancy, has_been_pregnant) in enumerate(test_cases, 1):
            print("=" * 80)
            print(f"📌 {nombre_caso} (Prueba {i}/{len(test_cases)})")
            print("=" * 80)
            
            try:
                # PASO 1: Crear un slot de prueba
                future_date = datetime.now() + timedelta(days=30)
                start_ts = int(future_date.timestamp())
                slot = await slot_repo.add_slot(
                    doctor_id=doctor_id,
                    start_ts=start_ts,
                    duration_min=30,
                    note=f"Slot de prueba para {nombre_caso}"
                )
                await session.flush()
                slot_id = slot.id
                print(f"  ✅ Slot creado: ID {slot_id}")
                
                # PASO 2: Guardar la cita usando book_slot (como en el flujo real)
                success = await appointment_repo.book_slot(
                    doctor_id=doctor_id,
                    slot_id=slot_id,
                    patient_telegram_id=test_user_id + i,  # IDs únicos para cada prueba
                    patient_name=f"Paciente Prueba {i}",
                    consultation_type=consultation_type,
                    reason=f"Prueba {nombre_caso}",
                    location="Ubicación de prueba",
                    status="pending",
                    is_first_pregnancy=is_first_pregnancy,
                    has_been_pregnant=has_been_pregnant
                )
                
                if not success:
                    print(f"  ❌ Error: No se pudo crear la cita")
                    resultados.append({
                        'caso': nombre_caso,
                        'exito': False,
                        'error': 'No se pudo crear la cita'
                    })
                    continue
                
                await session.commit()
                print(f"  ✅ Cita guardada exitosamente")
                
                # PASO 3: Obtener el appointment_id recién creado
                result = await session.execute(
                    select(Appointment).where(Appointment.slot_id == slot_id)
                )
                appointment = result.scalar_one_or_none()
                
                if not appointment:
                    print(f"  ❌ Error: No se encontró la cita creada")
                    resultados.append({
                        'caso': nombre_caso,
                        'exito': False,
                        'error': 'No se encontró la cita creada'
                    })
                    continue
                
                appointment_id = appointment.id
                appointment_ids_creados.append(appointment_id)
                print(f"  ✅ Appointment ID obtenido: {appointment_id}")
                
                # PASO 4: Cargar la cita usando get_appointment_by_id (como en el flujo real)
                appointment_data = await appointment_repo.get_appointment_by_id(
                    appointment_id, doctor_id
                )
                
                if not appointment_data:
                    print(f"  ❌ Error: No se pudo cargar la cita con get_appointment_by_id")
                    resultados.append({
                        'caso': nombre_caso,
                        'exito': False,
                        'error': 'No se pudo cargar la cita'
                    })
                    continue
                
                print(f"  ✅ Cita cargada con get_appointment_by_id")
                
                # PASO 5: Verificar que los valores se cargaron correctamente
                loaded_consultation_type = appointment_data.get('consultation_type')
                loaded_is_first = appointment_data.get('is_first_pregnancy')
                loaded_has_been = appointment_data.get('has_been_pregnant')
                
                print(f"\n  📊 Valores guardados vs cargados:")
                print(f"    consultation_type: '{consultation_type}' → '{loaded_consultation_type}' {'✅' if consultation_type == loaded_consultation_type else '❌'}")
                print(f"    is_first_pregnancy: {is_first_pregnancy} → {loaded_is_first} {'✅' if is_first_pregnancy == loaded_is_first else '❌'}")
                print(f"    has_been_pregnant: {has_been_pregnant} → {loaded_has_been} {'✅' if has_been_pregnant == loaded_has_been else '❌'}")
                
                # Verificar que todos los valores coinciden
                valores_correctos = (
                    consultation_type == loaded_consultation_type and
                    is_first_pregnancy == loaded_is_first and
                    has_been_pregnant == loaded_has_been
                )
                
                if not valores_correctos:
                    print(f"  ❌ Error: Los valores guardados no coinciden con los cargados")
                    resultados.append({
                        'caso': nombre_caso,
                        'exito': False,
                        'error': 'Valores no coinciden',
                        'guardados': {
                            'consultation_type': consultation_type,
                            'is_first_pregnancy': is_first_pregnancy,
                            'has_been_pregnant': has_been_pregnant
                        },
                        'cargados': {
                            'consultation_type': loaded_consultation_type,
                            'is_first_pregnancy': loaded_is_first,
                            'has_been_pregnant': loaded_has_been
                        }
                    })
                    continue
                
                # PASO 6: Simular decide_obstetric_flow con los valores cargados
                caso, descripcion, deberia_entrar_ho, formula = simulate_decide_obstetric_flow(
                    loaded_consultation_type, loaded_is_first, loaded_has_been
                )
                
                print(f"\n  🎯 Resultado de decide_obstetric_flow:")
                print(f"    Caso detectado: {caso}")
                print(f"    Descripción: {descripcion}")
                print(f"    ¿Entra a HO?: {'✅ SÍ' if deberia_entrar_ho else '❌ NO'}")
                if formula:
                    print(f"    Fórmula HO: {formula}")
                
                # Verificar que el caso detectado es el esperado
                caso_esperado = nombre_caso.split(':')[0].strip()
                if caso == caso_esperado:
                    print(f"  ✅ Caso detectado correctamente: {caso}")
                    resultados.append({
                        'caso': nombre_caso,
                        'exito': True,
                        'appointment_id': appointment_id,
                        'caso_detectado': caso,
                        'deberia_entrar_ho': deberia_entrar_ho,
                        'formula': formula
                    })
                else:
                    print(f"  ❌ Error: Se esperaba {caso_esperado} pero se detectó {caso}")
                    resultados.append({
                        'caso': nombre_caso,
                        'exito': False,
                        'error': f'Caso incorrecto: esperado {caso_esperado}, detectado {caso}'
                    })
                
            except Exception as e:
                print(f"  ❌ Error inesperado: {e}")
                import traceback
                traceback.print_exc()
                resultados.append({
                    'caso': nombre_caso,
                    'exito': False,
                    'error': str(e)
                })
            
            print()  # Línea en blanco entre pruebas
        
        # Limpiar: eliminar las citas y slots de prueba creados
        print("=" * 80)
        print("🧹 Limpiando datos de prueba...")
        print("=" * 80)
        
        for appointment_id in appointment_ids_creados:
            try:
                result = await session.execute(
                    select(Appointment).where(Appointment.id == appointment_id)
                )
                appointment = result.scalar_one_or_none()
                if appointment:
                    slot_id = appointment.slot_id
                    await session.delete(appointment)
                    # Eliminar el slot también
                    slot_result = await session.execute(
                        select(Slot).where(Slot.id == slot_id)
                    )
                    slot = slot_result.scalar_one_or_none()
                    if slot:
                        await session.delete(slot)
                    print(f"  ✅ Eliminada cita {appointment_id} y slot {slot_id}")
            except Exception as e:
                print(f"  ⚠️  Error al eliminar cita {appointment_id}: {e}")
        
        await session.commit()
        print("  ✅ Limpieza completada\n")
        
        # Resumen final
        print("=" * 80)
        print("📊 RESUMEN FINAL:")
        print("=" * 80)
        
        exitosos = sum(1 for r in resultados if r.get('exito'))
        fallidos = len(resultados) - exitosos
        
        print(f"  Total de pruebas: {len(resultados)}")
        print(f"  ✅ Exitosas: {exitosos}")
        print(f"  ❌ Fallidas: {fallidos}")
        
        if exitosos == len(resultados):
            print("\n  🎉 ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
        else:
            print("\n  ⚠️  Algunas pruebas fallaron:")
            for r in resultados:
                if not r.get('exito'):
                    print(f"    - {r['caso']}: {r.get('error', 'Error desconocido')}")
        
        print("\n" + "=" * 80)
        print("✅ Prueba completa finalizada")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_complete_obstetric_flow())

