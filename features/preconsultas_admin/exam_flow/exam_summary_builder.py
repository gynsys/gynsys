def build_summary_text(user_data: dict) -> str:
    """
    Construye un resumen médico ginecológico profesional basado en el flujo physical_exam_flow (3).json
    """
    parts = []

    # 1. CONDICIONES GENERALES Y ANTROPOMETRÍA
    general_parts = []
    if val := user_data.get('condiciones_generales'):
        general_parts.append(f"Paciente en {val.lower()} condiciones generales")
    
    # IMC calculado externamente
    if val := user_data.get('imc_calculado'):
        general_parts.append(f"IMC: {val}")

    if general_parts:
        parts.append(". ".join(general_parts) + ".")

    # 2. EXAMEN DE MAMAS - LÓGICA MEJORADA PARA AMBAS MAMAS
    mama_derecha_sim = user_data.get('mama_derecha_simetria')
    mama_izquierda_sim = user_data.get('mama_izquierda_simetria')
    
    # Verificar si ambas mamas son simétricas
    ambas_simetricas = (
        (mama_derecha_sim == "Simétrica" or mama_derecha_sim is None) and 
        (mama_izquierda_sim == "Simétrica" or mama_izquierda_sim is None)
    )
    
    # Verificar si hay hallazgos anormales en alguna mama
    hallazgos_anormales = False
    mama_derecha_parts = []
    mama_izquierda_parts = []
    
    # Evaluar mama derecha
    if mama_derecha_sim and mama_derecha_sim != "Simétrica":
        mama_derecha_parts.append(mama_derecha_sim.lower())
        hallazgos_anormales = True
    
    if val := user_data.get('mama_derecha_areola'):
        if val != "Normal":
            mama_derecha_parts.append(f"areola {val.lower()}")
            hallazgos_anormales = True
    
    if user_data.get('mama_derecha_nodulos') == 'Con Presencia':
        if radiales := user_data.get('mama_derecha_nodulos_radiales'):
            mama_derecha_parts.append(f"nódulo en radiales {radiales}")
        else:
            mama_derecha_parts.append("nódulos presentes")
        hallazgos_anormales = True
    
    if user_data.get('mama_derecha_secrecion') == 'Sí':
        mama_derecha_parts.append("secreción por pezón")
        hallazgos_anormales = True

    # Evaluar mama izquierda
    if mama_izquierda_sim and mama_izquierda_sim != "Simétrica":
        mama_izquierda_parts.append(mama_izquierda_sim.lower())
        hallazgos_anormales = True
    
    if val := user_data.get('mama_izquierda_areola'):
        if val != "Normal":
            mama_izquierda_parts.append(f"areola {val.lower()}")
            hallazgos_anormales = True
    
    if user_data.get('mama_izquierda_nodulos') == 'Con Presencia':
        if radiales := user_data.get('mama_izquierda_nodulos_radiales'):
            mama_izquierda_parts.append(f"nódulo en radiales {radiales}")
        else:
            mama_izquierda_parts.append("nódulos presentes")
        hallazgos_anormales = True
    
    if user_data.get('mama_izquierda_secrecion') == 'Sí':
        mama_izquierda_parts.append("secreción por pezón")
        hallazgos_anormales = True

    # Construir texto de mamas según los hallazgos
    if not hallazgos_anormales:
        # Si no hay hallazgos anormales y ambas son simétricas
        if ambas_simetricas:
            parts.append("Mamas: ambas simétricas, sin nódulos ni secreciones.")
        else:
            # Si no hay hallazgos anormales pero no tenemos información de simetría
            parts.append("Mamas: sin nódulos ni secreciones.")
    else:
        # Hay hallazgos anormales, detallar cada mama
        mamas_text = "Mamas: "
        if mama_derecha_parts:
            mamas_text += f"MD {', '.join(mama_derecha_parts)}"
        if mama_izquierda_parts:
            if mama_derecha_parts:
                mamas_text += "; "
            mamas_text += f"MI {', '.join(mama_izquierda_parts)}"
        parts.append(mamas_text + ".")

    # 3. EXAMEN GINECOLÓGICO - ESPÉCULO
    gineco_parts = []

    # Genitales externos
    if val := user_data.get('genitales_externos'):
        if val == "Normal":
            gineco_parts.append("genitales externos de configuración normal")
        else:
            gineco_parts.append("genitales externos de aspecto anormal")

    # Vagina
    vagina_desc = []
    
    # Trayecto vaginal
    if val := user_data.get('vagina_trayecto'):
        if val == "Sí":
            vagina_desc.append("trayecto libre")
        else:
            vagina_desc.append("trayecto no libre")
            
            # Buscar en las paredes vaginales posibles causas de obstrucción
            if paredes := user_data.get('paredes_vaginales'):
                paredes_lower = paredes.lower()
                if any(term in paredes_lower for term in ['tumor', 'masa']):
                    vagina_desc.append("con tumoración que obstruye lumen")
                elif 'tabique' in paredes_lower:
                    vagina_desc.append("con tabique vaginal")
                elif any(term in paredes_lower for term in ['estrechez', 'estenosis']):
                    vagina_desc.append("con estrechez marcada")
                elif any(term in paredes_lower for term in ['prolapso', 'cistocele', 'rectocele']):
                    vagina_desc.append("con prolapso que dificulta visualización")
    
    # Paredes vaginales
    if val := user_data.get('paredes_vaginales'):
        # Solo añadimos si no fue utilizada para explicar el trayecto no libre
        if not any(term in str(vagina_desc) for term in ['tumoración', 'tabique', 'estrechez', 'prolapso']):
            vagina_desc.append(f"paredes {val.lower()}")
    
    if vagina_desc:
        gineco_parts.append("vagina con " + ", ".join(vagina_desc))

    # Cuello uterino
    if val := user_data.get('cuello_uterino'):
        gineco_parts.append(f"cuello uterino {val.lower()}")

    # OCE (NUEVO - según el flujo actualizado)
    if val := user_data.get('oce_description'):
        if val == "Normal":
            gineco_parts.append("OCE de características normales")
        elif val == "Puntiforme (Nulípara)":
            gineco_parts.append("OCE puntiforme (nulípara)")
        elif val == "Transverso (Multípara)":
            gineco_parts.append("OCE transverso (multípara)")
        elif val == "No Valorable":
            gineco_parts.append("OCE no valorable")

    # Secreción vaginal
    secrecion_text = ""
    if tipos := user_data.get('secrecion_vaginal_tipo'):
        secrecion_parts = []
        
        if "Blanca" in tipos:
            if detalle := user_data.get('secrecion_blanca_detalle'):
                if detalle == "Fluida":
                    secrecion_parts.append("secreción blanquecina fluida")
                else:  # "Gruesa"
                    secrecion_parts.append("secreción blanquecina grumosa")
            else:
                secrecion_parts.append("secreción blanquecina")
        
        if "Con Sangrado" in tipos:
            if detalle := user_data.get('secrecion_sangre_detalle'):
                if detalle == "Con Coágulos Fétidos":
                    secrecion_parts.append("sangrado con coágulos fétidos")
                else:  # "Sin Coágulos Fétidos"
                    secrecion_parts.append("sangrado sin coágulos")
            else:
                secrecion_parts.append("sangrado activo")
        
        # Para otros tipos de secreción no especificados en el subflujo
        otros_tipos = [tipo.strip() for tipo in tipos.split(",") if tipo.strip() not in ["Blanca", "Con Sangrado"]]
        if otros_tipos:
            secrecion_parts.extend([f"secreción {tipo.lower()}" for tipo in otros_tipos])
        
        if secrecion_parts:
            secrecion_text = ", ".join(secrecion_parts)

    if secrecion_text:
        gineco_parts.append(secrecion_text)

    # Construir sección ginecológica con conectivos fluidos
    if gineco_parts:
        parts.append(", ".join(gineco_parts) + ".")

    # 4. TACTO VAGINAL (NUEVA SECCIÓN - según el flujo actualizado)
    if user_data.get('realizo_tacto') == 'Sí':
        tacto_parts = []
        
        # Posición del útero
        if val := user_data.get('utero_posicion'):
            if val == "AVF":
                tacto_parts.append("útero en anteversoflexión")
            elif val == "RVF":
                tacto_parts.append("útero en retroversoflexión")
            elif val == "Indiferente":
                tacto_parts.append("útero en posición indiferente")
        
        # Tamaño del útero
        if val := user_data.get('utero_tamano'):
            if val == "Normal, sup. regular":
                tacto_parts.append("útero de tamaño normal, superficie regular")
            elif val == "Aumentado, sup. regular":
                tacto_parts.append("útero aumentado de tamaño, superficie regular")
            elif val == "Aumentado, sup. irregular":
                tacto_parts.append("útero aumentado de tamaño, superficie irregular")
        
        # Movilización del cérvix
        if val := user_data.get('movilizacion_cervix'):
            if val == "No dolorosa":
                tacto_parts.append("movilización cervical no dolorosa")
            elif val == "Dolorosa":
                tacto_parts.append("movilización cervical dolorosa")
        
        # Anexos
        if val := user_data.get('anexos_hallazgos'):
            tacto_parts.append(f"anexos {val.lower()}")
        
        # Fondo de saco
        if val := user_data.get('fondo_saco'):
            if val == "Libre, no doloroso":
                tacto_parts.append("fondo de saco libre no doloroso")
            elif val == "Ocupado/Doloroso":
                tacto_parts.append("fondo de saco ocupado/doloroso")
        
        if tacto_parts:
            parts.append("Tacto vaginal: " + ", ".join(tacto_parts) + ".")
    elif user_data.get('realizo_tacto') == 'No':
        parts.append("No se realizó tacto vaginal.")

    # 5. INFORMACIÓN ADICIONAL
    if user_data.get('quiere_info_adicional') == 'Sí':
        if val := user_data.get('examen_fisico_adicional'):
            parts.append(f"Observaciones: {val}")

    # Unir todo en un texto coherente
    final_summary = " ".join(parts)

    # Si no hay datos, mensaje por defecto
    if not final_summary.strip():
        return "Examen físico sin hallazgos patológicos."

    return final_summary