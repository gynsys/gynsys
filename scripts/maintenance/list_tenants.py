"""
Script para listar y limpiar inquilinos (doctors) en la base de datos
"""
import sqlite3
from pathlib import Path
from datetime import datetime

# Ruta a la base de datos
DB_PATH = Path(__file__).resolve().parents[2] / "database" / "medical_bot.db"
SUPER_ADMIN_TELEGRAM_ID = 1035216286

def list_all_tenants():
    """Lista todos los inquilinos con información detallada"""
    if not DB_PATH.exists():
        print(f"❌ Error: No se encontró la base de datos en {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("📋 LISTADO DE INQUILINOS (DOCTORS)")
    print("=" * 80)
    print()
    
    # Consulta 1: Todos los médicos (activos e inactivos)
    print("🔹 TODOS LOS MÉDICOS (Activos e Inactivos):")
    print("-" * 80)
    cursor.execute('''
        SELECT id, name, telegram_id, is_active, created_at
        FROM doctors
        ORDER BY id DESC
    ''')
    
    doctors = cursor.fetchall()
    if not doctors:
        print("   No hay médicos registrados.")
    else:
        for doctor in doctors:
            id_db, name, telegram_id, is_active, created_at = doctor
            status = "✅ ACTIVO" if is_active else "❌ INACTIVO"
            print(f"   ID: {id_db:3d} | {status} | Telegram ID: {telegram_id:12d} | Nombre: {name}")
            if created_at:
                print(f"        Creado: {created_at}")
    
    print()
    print("=" * 80)
    
    # Consulta 2: Solo médicos activos
    print("🔹 MÉDICOS ACTIVOS:")
    print("-" * 80)
    cursor.execute('''
        SELECT id, name, telegram_id, created_at
        FROM doctors
        WHERE is_active = 1
        ORDER BY id DESC
    ''')
    
    active_doctors = cursor.fetchall()
    if not active_doctors:
        print("   No hay médicos activos.")
    else:
        for doctor in active_doctors:
            id_db, name, telegram_id, created_at = doctor
            print(f"   ID: {id_db:3d} | Telegram ID: {telegram_id:12d} | Nombre: {name}")
            if created_at:
                print(f"        Creado: {created_at}")
    
    print()
    print("=" * 80)
    
    # Consulta 3: Solo médicos inactivos
    print("🔹 MÉDICOS INACTIVOS:")
    print("-" * 80)
    cursor.execute('''
        SELECT id, name, telegram_id, created_at
        FROM doctors
        WHERE is_active = 0
        ORDER BY id DESC
    ''')
    
    inactive_doctors = cursor.fetchall()
    if not inactive_doctors:
        print("   No hay médicos inactivos.")
    else:
        for doctor in inactive_doctors:
            id_db, name, telegram_id, created_at = doctor
            print(f"   ID: {id_db:3d} | Telegram ID: {telegram_id:12d} | Nombre: {name}")
            if created_at:
                print(f"        Creado: {created_at}")
    
    print()
    print("=" * 80)
    
    # Consulta 4: Solicitudes de médicos
    print("🔹 SOLICITUDES DE MÉDICOS:")
    print("-" * 80)
    try:
        cursor.execute('''
            SELECT id, full_name, telegram_id, status, created_at
            FROM doctor_requests
            ORDER BY created_at DESC
        ''')
        
        requests = cursor.fetchall()
        if not requests:
            print("   No hay solicitudes registradas.")
        else:
            for req in requests:
                req_id, full_name, telegram_id, status, created_at = req
                status_emoji = {
                    'pending': '⏳',
                    'approved': '✅',
                    'rejected': '❌',
                    'deferred': '📋'
                }.get(status, '❓')
                print(f"   {status_emoji} ID: {req_id:3d} | {status.upper():10s} | Telegram ID: {telegram_id:12d} | Nombre: {full_name}")
                if created_at:
                    print(f"        Creado: {created_at}")
    except sqlite3.OperationalError:
        print("   La tabla 'doctor_requests' no existe aún.")
    
    print()
    print("=" * 80)
    
    # Estadísticas
    cursor.execute('SELECT COUNT(*) FROM doctors WHERE is_active = 1')
    active_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM doctors WHERE is_active = 0')
    inactive_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM doctors')
    total_count = cursor.fetchone()[0]
    
    print("📊 ESTADÍSTICAS:")
    print("-" * 80)
    print(f"   Total de médicos: {total_count}")
    print(f"   Médicos activos: {active_count}")
    print(f"   Médicos inactivos: {inactive_count}")
    print("=" * 80)
    
    conn.close()

def delete_doctor_by_id(doctor_id):
    """Elimina un médico por su ID de base de datos"""
    if not DB_PATH.exists():
        print(f"❌ Error: No se encontró la base de datos en {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verificar que existe
    cursor.execute('SELECT id, name, telegram_id FROM doctors WHERE id = ?', (doctor_id,))
    doctor = cursor.fetchone()
    
    if not doctor:
        print(f"❌ No se encontró un médico con ID {doctor_id}")
        conn.close()
        return False
    
    id_db, name, telegram_id = doctor
    
    # No permitir eliminar SuperAdmin
    if telegram_id == SUPER_ADMIN_TELEGRAM_ID:
        print(f"❌ No se puede eliminar al SuperAdmin")
        conn.close()
        return False
    
    # Eliminar asociaciones de pacientes
    cursor.execute('DELETE FROM patient_doctor WHERE doctor_id = ?', (doctor_id,))
    patients_deleted = cursor.rowcount
    
    # Eliminar información de contacto
    try:
        cursor.execute('DELETE FROM contact_info WHERE doctor_id = ?', (doctor_id,))
    except sqlite3.OperationalError:
        pass  # La tabla puede no existir
    
    # Eliminar el médico
    cursor.execute('DELETE FROM doctors WHERE id = ?', (doctor_id,))
    conn.commit()
    
    print(f"✅ Médico eliminado: ID {id_db} | {name} | Telegram ID: {telegram_id}")
    if patients_deleted > 0:
        print(f"   También se eliminaron {patients_deleted} asociaciones de pacientes")
    
    conn.close()
    return True

def delete_all_requests():
    """Elimina todas las solicitudes de médicos"""
    if not DB_PATH.exists():
        print(f"❌ Error: No se encontró la base de datos en {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT COUNT(*) FROM doctor_requests')
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("ℹ️  No hay solicitudes para eliminar")
            conn.close()
            return False
        
        cursor.execute('DELETE FROM doctor_requests')
        conn.commit()
        
        print(f"✅ Se eliminaron {count} solicitudes de médicos")
        conn.close()
        return True
    except sqlite3.OperationalError:
        print("ℹ️  La tabla 'doctor_requests' no existe")
        conn.close()
        return False

def delete_request_by_id(request_id):
    """Elimina una solicitud específica por ID"""
    if not DB_PATH.exists():
        print(f"❌ Error: No se encontró la base de datos en {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id, full_name, telegram_id FROM doctor_requests WHERE id = ?', (request_id,))
        request = cursor.fetchone()
        
        if not request:
            print(f"❌ No se encontró una solicitud con ID {request_id}")
            conn.close()
            return False
        
        req_id, full_name, telegram_id = request
        
        cursor.execute('DELETE FROM doctor_requests WHERE id = ?', (request_id,))
        conn.commit()
        
        print(f"✅ Solicitud eliminada: ID {req_id} | {full_name} | Telegram ID: {telegram_id}")
        conn.close()
        return True
    except sqlite3.OperationalError:
        print("ℹ️  La tabla 'doctor_requests' no existe")
        conn.close()
        return False

def delete_inactive_doctors():
    """Elimina todos los médicos inactivos (excepto SuperAdmin)"""
    if not DB_PATH.exists():
        print(f"❌ Error: No se encontró la base de datos en {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Obtener médicos inactivos
    cursor.execute('''
        SELECT id, name, telegram_id 
        FROM doctors 
        WHERE is_active = 0 AND telegram_id != ?
    ''', (SUPER_ADMIN_TELEGRAM_ID,))
    
    inactive_doctors = cursor.fetchall()
    
    if not inactive_doctors:
        print("ℹ️  No hay médicos inactivos para eliminar")
        conn.close()
        return False
    
    deleted_count = 0
    for doctor_id, name, telegram_id in inactive_doctors:
        # Eliminar asociaciones
        cursor.execute('DELETE FROM patient_doctor WHERE doctor_id = ?', (doctor_id,))
        
        # Eliminar información de contacto
        try:
            cursor.execute('DELETE FROM contact_info WHERE doctor_id = ?', (doctor_id,))
        except sqlite3.OperationalError:
            pass
        
        # Eliminar el médico
        cursor.execute('DELETE FROM doctors WHERE id = ?', (doctor_id,))
        deleted_count += 1
        print(f"   ✅ Eliminado: ID {doctor_id} | {name} | Telegram ID: {telegram_id}")
    
    conn.commit()
    print(f"\n✅ Se eliminaron {deleted_count} médicos inactivos")
    conn.close()
    return True

def reset_database():
    """Limpia toda la base de datos (excepto SuperAdmin)"""
    if not DB_PATH.exists():
        print(f"❌ Error: No se encontró la base de datos en {DB_PATH}")
        return False
    
    print("⚠️  ADVERTENCIA: Esta operación eliminará:")
    print("   - Todos los médicos (excepto SuperAdmin)")
    print("   - Todas las solicitudes")
    print("   - Todas las asociaciones paciente-médico")
    print("   - Toda la información de contacto")
    print()
    
    confirm = input("¿Estás seguro? Escribe 'SI' para confirmar: ")
    if confirm.upper() != 'SI':
        print("❌ Operación cancelada")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Eliminar asociaciones
    cursor.execute('DELETE FROM patient_doctor')
    patients_deleted = cursor.rowcount
    
    # Eliminar información de contacto
    try:
        cursor.execute('DELETE FROM contact_info')
    except sqlite3.OperationalError:
        pass
    
    # Eliminar solicitudes
    try:
        cursor.execute('DELETE FROM doctor_requests')
        requests_deleted = cursor.rowcount
    except sqlite3.OperationalError:
        requests_deleted = 0
    
    # Eliminar médicos (excepto SuperAdmin)
    cursor.execute('DELETE FROM doctors WHERE telegram_id != ?', (SUPER_ADMIN_TELEGRAM_ID,))
    doctors_deleted = cursor.rowcount
    
    conn.commit()
    
    print(f"\n✅ Base de datos limpiada:")
    print(f"   - Médicos eliminados: {doctors_deleted}")
    print(f"   - Solicitudes eliminadas: {requests_deleted}")
    print(f"   - Asociaciones eliminadas: {patients_deleted}")
    print(f"   - SuperAdmin preservado")
    
    conn.close()
    return True

def show_menu():
    """Muestra el menú de opciones"""
    print("\n" + "=" * 80)
    print("🧹 MENÚ DE LIMPIEZA DE BASE DE DATOS")
    print("=" * 80)
    print("1. Listar todos los inquilinos")
    print("2. Eliminar médico por ID")
    print("3. Eliminar solicitud por ID")
    print("4. Eliminar todas las solicitudes")
    print("5. Eliminar todos los médicos inactivos")
    print("6. Reset completo (elimina todo excepto SuperAdmin)")
    print("0. Salir")
    print("=" * 80)

def main():
    """Función principal con menú interactivo"""
    import sys
    
    if len(sys.argv) > 1:
        # Modo no interactivo: solo listar
        list_all_tenants()
        return
    
    while True:
        show_menu()
        choice = input("\nSelecciona una opción: ").strip()
        
        if choice == "0":
            print("👋 ¡Hasta luego!")
            break
        elif choice == "1":
            list_all_tenants()
        elif choice == "2":
            try:
                doctor_id = int(input("Ingresa el ID del médico a eliminar: "))
                delete_doctor_by_id(doctor_id)
            except ValueError:
                print("❌ Error: Debes ingresar un número válido")
            except KeyboardInterrupt:
                print("\n❌ Operación cancelada")
        elif choice == "3":
            try:
                request_id = int(input("Ingresa el ID de la solicitud a eliminar: "))
                delete_request_by_id(request_id)
            except ValueError:
                print("❌ Error: Debes ingresar un número válido")
            except KeyboardInterrupt:
                print("\n❌ Operación cancelada")
        elif choice == "4":
            confirm = input("¿Eliminar todas las solicitudes? (s/n): ")
            if confirm.lower() == 's':
                delete_all_requests()
            else:
                print("❌ Operación cancelada")
        elif choice == "5":
            confirm = input("¿Eliminar todos los médicos inactivos? (s/n): ")
            if confirm.lower() == 's':
                delete_inactive_doctors()
            else:
                print("❌ Operación cancelada")
        elif choice == "6":
            reset_database()
        else:
            print("❌ Opción no válida")
        
        input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    main()

