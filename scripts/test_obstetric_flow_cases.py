#!/usr/bin/env python3
"""
Script de prueba para los 4 casos del flujo obstétrico (HO).
Simula la lógica de decide_obstetric_flow usando datos reales de la base de datos.
"""
import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_PATH
from database.session import get_session
from database.models.appointment import Appointment
from sqlalchemy import select, desc
from features.preconsulta.flow_actions.services.formula_calculator import (
    get_primigesta_formula,
    get_nuligesta_formula
)

# Simular la función decide_obstetric_flow
def simulate_decide_obstetric_flow(consultation_type, is_first_pregnancy, has_been_pregnant):
    """
    Simula la lógica de decide_obstetric_flow.
    Retorna: (caso, resultado, deberia_entrar_ho, formula_ho)
    """
    user_data = {
        'consultation_type': consultation_type,
        'is_first_pregnancy': is_first_pregnancy,
        'has_been_pregnant': has_been_pregnant
    }
    
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


async def test_obstetric_flow_cases():
    """
    Prueba los 4 casos del flujo obstétrico usando datos reales de la base de datos.
    """
    print("=" * 80)
    print("🧪 PRUEBA: Flujo Obstétrico (HO) - 4 Casos")
    print("=" * 80)
    
    async with get_session() as session:
        # Usar consulta SQL directa para evitar problemas con columnas que no existen
        from sqlalchemy import text
        
        # Primero verificar si las columnas existen
        check_columns = text("""
            SELECT name FROM pragma_table_info('appointments') 
            WHERE name IN ('is_first_pregnancy', 'has_been_pregnant')
        """)
        result = await session.execute(check_columns)
        existing_columns = {row[0] for row in result.fetchall()}
        
        has_is_first = 'is_first_pregnancy' in existing_columns
        has_has_been = 'has_been_pregnant' in existing_columns
        
        print(f"\n📋 Estado de las columnas en la base de datos:")
        print(f"  - is_first_pregnancy: {'✅ Existe' if has_is_first else '❌ No existe'}")
        print(f"  - has_been_pregnant: {'✅ Existe' if has_has_been else '❌ No existe'}")
        
        if not has_is_first or not has_has_been:
            print("\n⚠️  ADVERTENCIA: Las columnas no existen en la base de datos.")
            print("   Ejecuta la migración: alembic upgrade head")
            print("   O el script usará valores None para estas columnas.\n")
        
        # Construir la consulta SQL según las columnas disponibles
        columns = [
            'id', 'slot_id', 'doctor_id', 'patient_telegram_id', 
            'patient_name', 'consultation_type', 'reason', 
            'location', 'status', 'booked_at'
        ]
        
        if has_is_first:
            columns.append('is_first_pregnancy')
        if has_has_been:
            columns.append('has_been_pregnant')
        
        columns_str = ', '.join(columns)
        sql_query = text(f"""
            SELECT {columns_str} 
            FROM appointments 
            ORDER BY id DESC 
            LIMIT 50
        """)
        
        result = await session.execute(sql_query)
        rows = result.fetchall()
        
        # Convertir a diccionarios
        appointments = []
        for row in rows:
            appt_dict = {}
            for i, col in enumerate(columns):
                appt_dict[col] = row[i]
            appointments.append(appt_dict)
        
        if not appointments:
            print("\n❌ No se encontraron citas en la base de datos.")
            return
        
        print(f"\n📋 Analizando {len(appointments)} citas...\n")
        
        # Contadores por caso
        casos_encontrados = {
            "CASO 1": [],
            "CASO 2": [],
            "CASO 3": [],
            "CASO 4": [],
            "FALLBACK": [],
            "DATOS_INCOMPLETOS": []
        }
        
        for appt in appointments:
            # Obtener valores del diccionario
            consultation_type = appt.get('consultation_type')
            is_first_pregnancy = appt.get('is_first_pregnancy')
            has_been_pregnant = appt.get('has_been_pregnant')
            
            # Convertir None/0/1 a bool si es necesario
            if is_first_pregnancy is not None:
                is_first_pregnancy = bool(is_first_pregnancy) if not isinstance(is_first_pregnancy, bool) else is_first_pregnancy
            if has_been_pregnant is not None:
                has_been_pregnant = bool(has_been_pregnant) if not isinstance(has_been_pregnant, bool) else has_been_pregnant
            
            # Verificar si los datos están completos
            datos_completos = True
            if consultation_type is None:
                datos_completos = False
            elif consultation_type == 'Prenatal' and is_first_pregnancy is None:
                datos_completos = False
            elif consultation_type == 'Ginecológica' and has_been_pregnant is None:
                datos_completos = False
            
            if not datos_completos:
                casos_encontrados["DATOS_INCOMPLETOS"].append({
                    'id': appt.get('id'),
                    'consultation_type': consultation_type,
                    'is_first_pregnancy': is_first_pregnancy,
                    'has_been_pregnant': has_been_pregnant,
                    'patient_name': appt.get('patient_name'),
                    'patient_id': appt.get('patient_telegram_id')
                })
                continue
            
            # Simular la lógica
            caso, descripcion, deberia_entrar_ho, formula = simulate_decide_obstetric_flow(
                consultation_type, is_first_pregnancy, has_been_pregnant
            )
            
            casos_encontrados[caso].append({
                'id': appt.get('id'),
                'descripcion': descripcion,
                'deberia_entrar_ho': deberia_entrar_ho,
                'formula': formula,
                'consultation_type': consultation_type,
                'is_first_pregnancy': is_first_pregnancy,
                'has_been_pregnant': has_been_pregnant,
                'patient_name': appt.get('patient_name'),
                'patient_id': appt.get('patient_telegram_id')
            })
        
        # Mostrar resultados
        print("\n" + "=" * 80)
        print("📊 RESULTADOS POR CASO:")
        print("=" * 80)
        
        for caso, citas in casos_encontrados.items():
            if not citas:
                continue
            
            print(f"\n{'=' * 80}")
            print(f"📌 {caso}: {len(citas)} cita(s)")
            print("=" * 80)
            
            for cita in citas:
                print(f"\n  Cita ID: {cita['id']}")
                print(f"  Paciente: {cita.get('patient_name', 'N/A')} (ID: {cita.get('patient_id', 'N/A')})")
                print(f"  Tipo Consulta: {cita.get('consultation_type', 'N/A')}")
                print(f"  is_first_pregnancy: {cita.get('is_first_pregnancy', 'N/A')}")
                print(f"  has_been_pregnant: {cita.get('has_been_pregnant', 'N/A')}")
                
                if caso != "DATOS_INCOMPLETOS":
                    print(f"  Descripción: {cita.get('descripcion', 'N/A')}")
                    print(f"  ¿Debería entrar a HO?: {'✅ SÍ' if cita.get('deberia_entrar_ho') else '❌ NO'}")
                    if cita.get('formula'):
                        print(f"  Fórmula HO asignada: {cita['formula']}")
                else:
                    print(f"  ⚠️  DATOS INCOMPLETOS - No se puede determinar el caso")
        
        # Resumen estadístico
        print("\n" + "=" * 80)
        print("📈 RESUMEN ESTADÍSTICO:")
        print("=" * 80)
        total = sum(len(citas) for citas in casos_encontrados.values())
        print(f"  Total de citas analizadas: {total}")
        print(f"  CASO 1 (Prenatal-Primigesta): {len(casos_encontrados['CASO 1'])}")
        print(f"  CASO 2 (Prenatal-Multigesta): {len(casos_encontrados['CASO 2'])}")
        print(f"  CASO 3 (Ginecológica-Nuligesta): {len(casos_encontrados['CASO 3'])}")
        print(f"  CASO 4 (Ginecológica con historial): {len(casos_encontrados['CASO 4'])}")
        print(f"  FALLBACK (No determinado): {len(casos_encontrados['FALLBACK'])}")
        print(f"  ⚠️  Datos incompletos: {len(casos_encontrados['DATOS_INCOMPLETOS'])}")
        
        # Pruebas de casos específicos
        print("\n" + "=" * 80)
        print("🧪 PRUEBAS DE CASOS ESPECÍFICOS:")
        print("=" * 80)
        
        casos_test = [
            ("CASO 1", "Prenatal", True, None),
            ("CASO 2", "Prenatal", False, None),
            ("CASO 3", "Ginecológica", None, False),
            ("CASO 4", "Ginecológica", None, True),
        ]
        
        for nombre_caso, ct, ifp, hbp in casos_test:
            caso, descripcion, deberia_entrar_ho, formula = simulate_decide_obstetric_flow(ct, ifp, hbp)
            print(f"\n  {nombre_caso}:")
            print(f"    Input: consultation_type='{ct}', is_first_pregnancy={ifp}, has_been_pregnant={hbp}")
            print(f"    Resultado: {descripcion}")
            print(f"    ¿Entra a HO?: {'✅ SÍ' if deberia_entrar_ho else '❌ NO'}")
            if formula:
                print(f"    Fórmula: {formula}")
        
        print("\n" + "=" * 80)
        print("✅ Pruebas completadas")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_obstetric_flow_cases())

