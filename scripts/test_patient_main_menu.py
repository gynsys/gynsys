"""
Script de prueba para simular el flujo de finish_preconsultation -> patient_main_menu
sin modificar archivos del proyecto.

Este script simula exactamente el escenario donde finish_preconsultation
crea un FakeUpdate y llama a patient_main_menu.
"""
import sys
import asyncio
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from features.patient_menu.patient_handler import patient_main_menu
from config import DB_PATH


class FakeUser:
    """Simula un usuario de Telegram"""
    def __init__(self, user_id: int, first_name: str = "Test User"):
        self.id = user_id
        self.first_name = first_name


class FakeChat:
    """Simula un chat de Telegram"""
    def __init__(self, chat_id: int):
        self.id = chat_id


class FakeUpdate:
    """Simula el FakeUpdate que se crea en finish_preconsultation"""
    def __init__(self, chat_id: int, user_id: int, first_name: str = "Test User"):
        self.effective_chat = FakeChat(chat_id)
        self.effective_user = FakeUser(user_id, first_name)
        self.message = None  # Esto es None en finish_preconsultation
        self.callback_query = None


class FakeBot:
    """Simula el bot de Telegram para enviar mensajes"""
    async def send_message(self, chat_id: int, text: str, reply_markup=None, parse_mode=None):
        print("\n" + "="*60)
        print("📤 MENSAJE ENVIADO AL BOT:")
        print("="*60)
        print(f"Chat ID: {chat_id}")
        print(f"Parse Mode: {parse_mode}")
        print(f"\nContenido del mensaje:")
        print("-" * 60)
        print(text)
        print("-" * 60)
        if reply_markup:
            print(f"\nTeclado: {len(reply_markup.inline_keyboard)} filas de botones")
            for i, row in enumerate(reply_markup.inline_keyboard):
                buttons = [btn.text for btn in row]
                print(f"  Fila {i+1}: {', '.join(buttons)}")
        print("="*60 + "\n")
        return type('obj', (object,), {'message_id': 12345})()


class FakeContext:
    """Simula el context de Telegram"""
    def __init__(self, bot: FakeBot):
        self.bot = bot
        self.user_data = {}


async def test_patient_main_menu():
    """Función de prueba principal"""
    print("🧪 Iniciando prueba de patient_main_menu con FakeUpdate")
    print("-" * 60)
    
    # Configuración de prueba
    # Ajusta estos valores según tu base de datos
    TEST_CHAT_ID = 1113298656 # ID del chat de prueba
    TEST_USER_ID = 5618424590 # ID del usuario de prueba
    TEST_DOCTOR_ID = 5  # ID del doctor en la BD (ajusta según tu BD)
    TEST_USER_NAME = "Paciente Prueba"
    
    print(f"📋 Configuración de prueba:")
    print(f"   Chat ID: {TEST_CHAT_ID}")
    print(f"   User ID: {TEST_USER_ID}")
    print(f"   Doctor ID: {TEST_DOCTOR_ID}")
    print(f"   User Name: {TEST_USER_NAME}")
    print("-" * 60)
    
    # Crear objetos simulados (igual que en finish_preconsultation)
    fake_update = FakeUpdate(TEST_CHAT_ID, TEST_USER_ID, TEST_USER_NAME)
    fake_bot = FakeBot()
    fake_context = FakeContext(fake_bot)
    
    print(f"\n✅ FakeUpdate creado:")
    print(f"   - effective_chat.id: {fake_update.effective_chat.id}")
    print(f"   - effective_user.id: {fake_update.effective_user.id}")
    print(f"   - effective_user.first_name: {fake_update.effective_user.first_name}")
    print(f"   - message: {fake_update.message}")
    print(f"   - callback_query: {fake_update.callback_query}")
    
    try:
        # Llamar a patient_main_menu (igual que en finish_preconsultation)
        print(f"\n🚀 Llamando a patient_main_menu...")
        await patient_main_menu(fake_update, fake_context, TEST_DOCTOR_ID)
        print("\n✅ Prueba completada exitosamente!")
        
    except Exception as e:
        print(f"\n❌ Error durante la prueba:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensaje: {str(e)}")
        import traceback
        print(f"\n📋 Traceback completo:")
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 SCRIPT DE PRUEBA: patient_main_menu con FakeUpdate")
    print("="*60)
    print("\nEste script simula el escenario donde finish_preconsultation")
    print("crea un FakeUpdate y llama a patient_main_menu.\n")
    
    # Ejecutar la prueba
    success = asyncio.run(test_patient_main_menu())
    
    print("\n" + "="*60)
    if success:
        print("✅ PRUEBA EXITOSA")
    else:
        print("❌ PRUEBA FALLIDA")
    print("="*60 + "\n")
    
    sys.exit(0 if success else 1)

