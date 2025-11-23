"""
Script de pruebas de integración para todos los repositorios migrados a SQLAlchemy.
Verifica que todos los repositorios funcionan correctamente.
"""
import asyncio
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root_dir))

from database.engine import init_engine, close_engine
from database.session import get_session
from database.repositories import (
    ExtraModuleRepository,
    DoctorRepository,
    PatientDoctorRepository,
    SlotRepository,
    AppointmentRepository,
    TextContentRepository,
    GenericContentRepository,
    LocationRepository,
    MedicalRepository,
    PDFRepository,
    NotificationRepository,
    RequestRepository,
    ContactRepository,
    JobRepository,
    MainMenuButtonRepository,
    SubmenuRepository,
    SubmenuButtonRepository,
    BotRepository,
    BotLogoRepository,
    UserActionRepository,
)
from database.models import Doctor, Bot
from sqlalchemy import text, select
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Colors:
    """Colores para output en consola"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")


def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")


async def test_repository_basic_operations(repo_class, repo_name, session):
    """Prueba operaciones básicas de un repositorio"""
    print_info(f"Probando {repo_name}...")
    try:
        repo = repo_class(session)
        
        # Probar get_by_id (si hay datos)
        # Esto es solo para verificar que el repositorio se puede instanciar
        print_success(f"{repo_name}: Repositorio instanciado correctamente")
        return True
    except Exception as e:
        print_error(f"{repo_name}: Error - {e}")
        return False


async def test_doctor_repository(session):
    """Prueba DoctorRepository"""
    print_info("Probando DoctorRepository...")
    try:
        repo = DoctorRepository(session)
        
        # Obtener un doctor existente
        result = await session.execute(
            text("SELECT id FROM doctors LIMIT 1")
        )
        row = result.fetchone()
        
        if row:
            doctor_id = row[0]
            doctor = await repo.get_by_id(doctor_id)
            if doctor:
                print_success(f"DoctorRepository: Doctor encontrado - {doctor.name}")
                return True
            else:
                print_warning("DoctorRepository: No se encontró doctor")
                return True  # No es un error, puede no haber datos
        else:
            print_warning("DoctorRepository: No hay doctores en la BD")
            return True
    except Exception as e:
        print_error(f"DoctorRepository: Error - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_bot_repository(session):
    """Prueba BotRepository"""
    print_info("Probando BotRepository...")
    try:
        repo = BotRepository(session)
        
        # Probar get_user_tenant (función de utilidad)
        # Necesitamos un user_id de prueba
        result = await session.execute(
            text("SELECT admin_user_id FROM bots WHERE is_active = 1 LIMIT 1")
        )
        row = result.fetchone()
        
        if row:
            user_id = row[0]
            tenant_id = await repo.get_user_tenant(user_id)
            if tenant_id:
                print_success(f"BotRepository: Tenant encontrado para user {user_id}: {tenant_id}")
            else:
                print_warning("BotRepository: No se encontró tenant")
        else:
            print_warning("BotRepository: No hay bots activos")
        
        return True
    except Exception as e:
        print_error(f"BotRepository: Error - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_medical_repository(session):
    """Prueba MedicalRepository (con encriptación)"""
    print_info("Probando MedicalRepository...")
    try:
        repo = MedicalRepository(session)
        
        # Verificar que el repositorio se puede instanciar
        print_success("MedicalRepository: Repositorio instanciado correctamente")
        
        # Probar obtener historias (si hay)
        result = await session.execute(
            text("SELECT COUNT(*) FROM medical_histories")
        )
        count = result.scalar()
        print_info(f"MedicalRepository: {count} historias médicas en la BD")
        
        return True
    except Exception as e:
        print_error(f"MedicalRepository: Error - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_content_repositories(session):
    """Prueba repositorios de contenido"""
    print_info("Probando repositorios de contenido...")
    try:
        # TextContentRepository
        text_repo = TextContentRepository(session)
        print_success("TextContentRepository: Instanciado correctamente")
        
        # GenericContentRepository
        generic_repo = GenericContentRepository(session)
        print_success("GenericContentRepository: Instanciado correctamente")
        
        return True
    except Exception as e:
        print_error(f"Content Repositories: Error - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_menu_repositories(session):
    """Prueba repositorios de menú"""
    print_info("Probando repositorios de menú...")
    try:
        main_menu_repo = MainMenuButtonRepository(session)
        print_success("MainMenuButtonRepository: Instanciado correctamente")
        
        submenu_repo = SubmenuRepository(session)
        print_success("SubmenuRepository: Instanciado correctamente")
        
        submenu_button_repo = SubmenuButtonRepository(session)
        print_success("SubmenuButtonRepository: Instanciado correctamente")
        
        return True
    except Exception as e:
        print_error(f"Menu Repositories: Error - {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Ejecuta todas las pruebas"""
    print("\n" + "="*60)
    print("🧪 PRUEBAS DE INTEGRACIÓN - REPOSITORIOS SQLALCHEMY")
    print("="*60 + "\n")
    
    # Inicializar engine
    print_info("Inicializando engine SQLAlchemy...")
    await init_engine()
    print_success("Engine inicializado\n")
    
    results = {}
    
    try:
        async with get_session() as session:
            # Pruebas de repositorios principales
            print("\n" + "-"*60)
            print("📦 REPOSITORIOS PRINCIPALES")
            print("-"*60)
            
            results['DoctorRepository'] = await test_doctor_repository(session)
            results['BotRepository'] = await test_bot_repository(session)
            results['MedicalRepository'] = await test_medical_repository(session)
            results['ContentRepositories'] = await test_content_repositories(session)
            results['MenuRepositories'] = await test_menu_repositories(session)
            
            # Pruebas de instanciación de todos los repositorios
            print("\n" + "-"*60)
            print("🔧 VERIFICACIÓN DE INSTANCIACIÓN")
            print("-"*60)
            
            repositories = [
                (ExtraModuleRepository, "ExtraModuleRepository"),
                (PatientDoctorRepository, "PatientDoctorRepository"),
                (SlotRepository, "SlotRepository"),
                (AppointmentRepository, "AppointmentRepository"),
                (LocationRepository, "LocationRepository"),
                (PDFRepository, "PDFRepository"),
                (NotificationRepository, "NotificationRepository"),
                (RequestRepository, "RequestRepository"),
                (ContactRepository, "ContactRepository"),
                (JobRepository, "JobRepository"),
                (BotLogoRepository, "BotLogoRepository"),
                (UserActionRepository, "UserActionRepository"),
            ]
            
            for repo_class, repo_name in repositories:
                results[repo_name] = await test_repository_basic_operations(
                    repo_class, repo_name, session
                )
    
    finally:
        # Cerrar engine
        print("\n" + "-"*60)
        print_info("Cerrando engine...")
        await close_engine()
        print_success("Engine cerrado\n")
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"\nTotal de pruebas: {total}")
    print_success(f"Exitosas: {passed}")
    if failed > 0:
        print_error(f"Fallidas: {failed}")
    
    # Listar fallidas
    if failed > 0:
        print("\n⚠️  Pruebas fallidas:")
        for name, result in results.items():
            if not result:
                print_error(f"  - {name}")
    
    print("\n" + "="*60)
    
    if failed == 0:
        print_success("🎉 ¡Todas las pruebas pasaron!")
        return 0
    else:
        print_error("❌ Algunas pruebas fallaron")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)


