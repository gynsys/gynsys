# common/pdf/summary_report.py
# Generación de PDF para Informe Médico Resumido
import io
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.units import inch
from reportlab.lib import colors

from features.pdf_configuration.database import get_pdf_settings
from .summary_builder import build_narrative_summary
from .utils import create_logo_image, create_qr_image

logger = logging.getLogger(__name__)

# Meses en español
SPANISH_MONTHS = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
}

def format_date_spanish(date: datetime = None) -> str:
    """Formatea una fecha en español: 'dd de mes de yyyy'"""
    if date is None:
        date = datetime.now()
    day = date.day
    month = SPANISH_MONTHS[date.month]
    year = date.year
    return f"{day} de {month} de {year}"


async def generate_summary_report(report_data: dict, doctor_id: int) -> bytes:
    """
    Genera el PDF del Informe Médico Resumido (tamaño carta).
    """
    # Verificar si el examen funcional está habilitado para este doctor
    pdf_settings = await get_pdf_settings(doctor_id)
    include_functional_exam = pdf_settings.get('include_functional_exam', {}).get('value', '1') == '1'
    
    # Pasar la configuración al builder para que respete si está deshabilitado
    report_context = build_narrative_summary(report_data, include_functional_exam=include_functional_exam)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch, leftMargin=0.75*inch, rightMargin=0.75*inch)
    story = []

    styles = getSampleStyleSheet()
    styleN = ParagraphStyle(name='Normal', fontName='Helvetica', fontSize=12, leading=14)
    styleB = ParagraphStyle(name='Bold', fontName='Helvetica-Bold', fontSize=12, leading=14)
    styleH1 = ParagraphStyle(name='Heading1', fontName='Helvetica-Bold', fontSize=14, alignment=TA_CENTER, spaceAfter=6)

    style_narrative = ParagraphStyle(
        name='Narrative',
        parent=styleN,
        alignment=TA_JUSTIFY,
        leading=20,
        firstLineIndent=0   # Sin sangría inicial para el texto narrativo
    )
    
    # Estilo para el plan numerado (1., 2., etc.)
    style_plan = ParagraphStyle(
        name='Plan',
        parent=styleN,
        alignment=TA_JUSTIFY,  # Justificado como el texto narrativo
        leading=16,
        leftIndent=18,      # Sangría izquierda para los números
        firstLineIndent=0 # Compensar la primera línea para alinear números
    )
    style_patient_data = ParagraphStyle(name='PatientData', parent=styleN, spaceAfter=2)

    pdf_settings = await get_pdf_settings(doctor_id)
    def get_pdf_setting(setting_key, default=''):
        setting = pdf_settings.get(setting_key, {})
        if not setting.get('visible', True): return None
        return setting.get('value', default)

    logo_header_1_path = get_pdf_setting('logo_header_1')
    logo_header_2_path = get_pdf_setting('logo_header_2')
    header_parts = []
    doctor_name = get_pdf_setting('doctor_name', 'Dra. Mariel Herrera')
    if doctor_name: header_parts.append(f"<b>{doctor_name}</b>")
    specialty = get_pdf_setting('specialty', 'Especialista en Ginecología y Obstetricia')
    if specialty: header_parts.append(specialty)
    location = get_pdf_setting('location', 'Caracas-Guarenas Guatire')
    if location: header_parts.append(location)
    phones = get_pdf_setting('phones', '04244281876-04127738918')
    if phones: header_parts.append(f"Citas: {phones}")
    header_text = "<br/>".join(header_parts)
    logo_left = create_logo_image(logo_header_1_path)
    logo_right = create_logo_image(logo_header_2_path)
    
    # Crear payload y QR para el encabezado
    validation_payload = {
        "doctor": doctor_name,
        "mpps": get_pdf_setting('mpps_number'),
        "cmdm": get_pdf_setting('cmdm_number'),
        "doctor_id": doctor_id,
        "patient": {
            "name": report_context.get('full_name'),
            "ci": report_context.get('ci')
        },
        "history_number": report_context.get('history_number', 'N/A'),
        "generated_at": datetime.utcnow().isoformat(),
    }
    qr_image = create_qr_image(validation_payload)
    
    # Crear bloque QR con texto para el encabezado (parte superior derecha)
    # 2mm a la derecha = 0.079 inches (anteriormente estaba -8mm, ahora +2mm = neto -6mm = -0.236 inches)
    qr_caption_header = Paragraph(
        "Escanea si deseas validar",
        ParagraphStyle(name='QRHeaderNote', fontSize=7, alignment=TA_CENTER, leftIndent=-0.236*inch)
    )
    
    # Columna derecha del encabezado: logo derecho arriba, QR abajo
    right_column_elements = []
    if logo_right:
        right_column_elements.append(logo_right)
        right_column_elements.append(Spacer(1, 0.1*inch))
    if qr_image:
        right_column_elements.append(qr_image)
        right_column_elements.append(Spacer(1, 0.02*inch))
        right_column_elements.append(qr_caption_header)
    
    # Si no hay logo derecho ni QR, usar espacio vacío
    right_column_content = right_column_elements if right_column_elements else [""]
    
    header_data = [[logo_left, Paragraph(header_text, styleN), right_column_content]]
    header_table = Table(header_data, colWidths=[1*inch, 5.5*inch, 1*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), 
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('LEFTPADDING', (1, 0), (1, 0), 0.197*inch),  # Mover bloque de datos del doctor 5mm a la derecha
        ('LEFTPADDING', (2, 0), (2, 0), -0.5*inch),  # Mover QR 1/2 pulgada a la izquierda
    ]))
    story.append(header_table)

    line_table = Table([['']], colWidths=[7.5*inch])
    line_table.setStyle(TableStyle([('LINEBELOW', (0,0), (-1,-1), 1, colors.black)]))
    story.append(line_table)
    story.append(Spacer(1, 0.25*inch))
    story.append(Paragraph("<u>INFORME MÉDICO</u>", styleH1))
    story.append(Spacer(1, 0.25*inch))

    story.append(Paragraph(f"<b>Nombre y Apellidos:</b> {report_context.get('full_name')}", style_patient_data))
    story.append(Paragraph(f"<b>Edad:</b> {report_context.get('age')}", style_patient_data))
    story.append(Paragraph(f"<b>C.I.:</b> {report_context.get('ci')}", style_patient_data))
    story.append(Spacer(1, 0.3*inch))

    narrative_content = report_context.get('narrative_summary')
    if narrative_content:
        # Separar el texto narrativo del plan (que tiene viñetas)
        # El plan comienza después de "Se indica como plan:"
        plan_marker = "Se indica como plan:"
        
        if plan_marker in narrative_content:
            # Dividir en texto narrativo y plan
            parts = narrative_content.split(plan_marker, 1)
            narrative_text = parts[0].strip()
            plan_text = parts[1].strip() if len(parts) > 1 else None
            
            # Renderizar texto narrativo
            if narrative_text:
                narrative_paragraph = Paragraph(narrative_text, style_narrative)
                story.append(narrative_paragraph)
            
            # Renderizar el texto "Se indica como plan:" y luego el plan
            if plan_text:
                # Primero el texto introductorio
                intro_paragraph = Paragraph("Se indica como plan:", style_narrative)
                story.append(intro_paragraph)
                
                # Renderizar cada item del plan por separado para asegurar sangría correcta
                # Dividir por <br/> para obtener cada item
                plan_items = [item.strip() for item in plan_text.split('<br/>') if item.strip()]
                for item in plan_items:
                    plan_item_paragraph = Paragraph(item, style_plan)
                    story.append(plan_item_paragraph)
        else:
            # No hay plan, solo texto narrativo
            narrative_paragraph = Paragraph(narrative_content, style_narrative)
            story.append(narrative_paragraph)

    story.append(Spacer(1, 0.3*inch))
    footer_city = get_pdf_setting('footer_city', 'Guarenas')
    today_str = format_date_spanish()
    pre_signature_text = f"Sin otro particular se suscribe en {footer_city} a los {today_str}."
    story.append(Paragraph(pre_signature_text, ParagraphStyle(name='PreFooter', fontSize=12, alignment=TA_CENTER, spaceAfter=24)))

    signature_path = get_pdf_setting('logo_signature')
    signature_img = create_logo_image(signature_path, width=2.5*inch, height=1*inch)
    # QR ya se creó arriba para el encabezado, no es necesario crearlo de nuevo
    signature_block = signature_img if signature_img else Paragraph(
        "_________________________",
        ParagraphStyle(name='SignatureLine', alignment=TA_CENTER)
    )
    if signature_img:
        signature_img.hAlign = 'CENTER'

    post_signature_parts = []
    if doctor_name:
        post_signature_parts.append(f"<b>{doctor_name}</b>")
    post_signature_parts.append("Ginecólogo Obstetra - UCV")
    mpps_number, cmdm_number = get_pdf_setting('mpps_number'), get_pdf_setting('cmdm_number')
    if mpps_number and cmdm_number:
        post_signature_parts.append(f"MPPS: {mpps_number} / CMDM: {cmdm_number}")
    doctor_id = get_pdf_setting('doctor_id')
    if doctor_id:
        post_signature_parts.append(f"C.I.: {doctor_id}")
    post_signature_text = "<br/>".join(post_signature_parts)
    doctor_info_para = Paragraph(
        post_signature_text,
        ParagraphStyle(name='PostFooter', fontSize=10, alignment=TA_CENTER, leading=12)
    )

    # Solo la firma y datos del médico (sin QR, ya está en el encabezado)
    signature_column = [signature_block, Spacer(1, 0.05*inch), doctor_info_para]

    # Firma y datos del médico centrados (sin wrapper que desplaza a la derecha)
    signature_table = Table([[signature_column]], colWidths=[7.5*inch])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (0, 0), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(signature_table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

