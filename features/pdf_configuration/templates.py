# features/pdf_configuration/templates.py
from common.helpers import escape_html

async def get_configuration_text(settings: dict) -> str:
    """Genera el texto de la interfaz de configuración"""
    
    text = "📄 <b>Configuración del Informe PDF</b>\n\n"
    
    # Sección: Datos del Médico
    text += "👨‍⚕️ <b>DATOS DEL MÉDICO:</b>\n"
    medical_fields = [
        ('doctor_name', 'Nombre'),
        ('specialty', 'Especialidad'),
        ('location', 'Ubicación'),
        ('phones', 'Teléfonos'),
        ('mpps_number', 'MPPS'),
        ('cmdm_number', 'CMDM'),
        ('doctor_id', 'C.I. Médico')
    ]
    
    for key, label in medical_fields:
        setting = settings.get(key, {})
        value = setting.get('value', 'No configurado')
        visible = setting.get('visible', True)
        visibility_icon = "👁️" if visible else "👁️‍🗨️"
        text += f"{visibility_icon} <b>{label}:</b> {escape_html(str(value))}\n"
    
    text += "\n"
    
    # Sección: Encabezado y Pie
    text += "📝 <b>ENCABEZADO Y PIE:</b>\n"
    header_fields = [
        ('report_title', 'Título del Informe'),
        ('footer_city', 'Ciudad del Pie')
    ]
    
    for key, label in header_fields:
        setting = settings.get(key, {})
        value = setting.get('value', 'No configurado')
        visible = setting.get('visible', True)
        visibility_icon = "👁️" if visible else "👁️‍🗨️"
        text += f"{visibility_icon} <b>{label}:</b> {escape_html(str(value))}\n"
    
    text += "\n"
    
    # Sección: Logos y Firmas
    text += "🖼️ <b>LOGOS Y FIRMAS:</b>\n"
    logo_fields = [
        ('logo_header_1', 'Logo Superior Izquierdo'),
        ('logo_header_2', 'Logo Superior Derecho'),
        ('logo_signature', 'Firma y Sello')
    ]
    
    for key, label in logo_fields:
        setting = settings.get(key, {})
        value = setting.get('value')
        visible = setting.get('visible', True)
        visibility_icon = "👁️" if visible else "👁️‍🗨️"
        
        status = "✅ Cargado" if value else "❌ No cargado"
        text += f"{visibility_icon} <b>{label}:</b> {status}\n"
    
    text += "\n💡 <i>Usa los botones para editar cada campo. El icono 👁️ controla si se muestra en el PDF.</i>"
    
    return text

def get_edit_field_text(field_name: str, current_value: str) -> str:
    """Texto para editar un campo específico"""
    return f"✍️ <b>Editando: {field_name}</b>\n\nValor actual: <code>{escape_html(str(current_value))}</code>\n\nEnvía el nuevo valor o escribe 'cancelar' para abortar:"

def get_upload_logo_text(logo_type: str) -> str:
    """Texto para subir un logo"""
    logo_names = {
        'logo_header_1': 'Logo Superior Izquierdo',
        'logo_header_2': 'Logo Superior Derecho', 
        'logo_signature': 'Firma y Sello'
    }
    return f"📤 <b>Subiendo: {logo_names.get(logo_type, logo_type)}</b>\n\nEnvía la imagen o escribe 'cancelar' para abortar:"

def get_delete_confirmation_text(logo_type: str) -> str:
    """Texto para confirmar eliminación"""
    logo_names = {
        'logo_header_1': 'Logo Superior Izquierdo',
        'logo_header_2': 'Logo Superior Derecho',
        'logo_signature': 'Firma y Sello'
    }
    return f"⚠️ <b>¿Eliminar {logo_names.get(logo_type, logo_type)}?</b>\n\nEsta acción no se puede deshacer."

def get_preview_generating_text() -> str:
    """Texto mientras se genera la vista previa"""
    return "⏳ <b>Generando vista previa del PDF...</b>\n\nEsto puede tomar unos segundos."