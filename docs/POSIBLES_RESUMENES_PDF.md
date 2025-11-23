# Posibles Resúmenes para PDFs - Historia Médica e Informe Médico

Este documento muestra todos los posibles resúmenes que se pueden construir con las funciones actuales para los PDFs de historia médica completa e informe médico resumido.

---

## 📋 **HISTORIA MÉDICA COMPLETA** (Tamaño Oficio)

La historia médica completa usa **3 resúmenes separados** que se muestran en secciones distintas:

### 1. **Antecedentes Obstétricos y Ginecológicos** (`summary_gyn_obstetric`)

Función: `_build_gyn_summary(user_data)`

#### Escenario 1: Paciente Nuligesta
```
Paciente nuligesta. Menarquía a los 12 años y sexarquía a los 18. Refiere ciclos menstruales regulares, sin dismenorrea. No mantiene actividad sexual actualmente.
```

#### Escenario 2: Paciente Primigesta
```
Paciente primigesta. Menarquía a los 13 años y sexarquía a los 17. Refiere ciclos menstruales regulares, sin dismenorrea. Mantiene actividad sexual activa sin deseo de fertilidad.
```

#### Escenario 3: Paciente con Gestaciones (IG, IIP, etc.)
```
Paciente con IG -> 2020 3.2 kg / 50 cm, que cursó Sin complicaciones. Menarquía a los 14 años y sexarquía a los 19. Refiere ciclos menstruales irregulares con duración de 28-35 días y frecuencia de cada 30-40 días, asociados a dismenorrea de intensidad 7/10. Su FUM fue el 15/11/2024. Utiliza como método anticonceptivo: pastillas. Mantiene actividad sexual activa con deseo de fertilidad no logrado. Su último control ginecológico fue en noviembre del 2023. Su última citología fue realizada en noviembre del 2023.
```

#### Escenario 4: Paciente con Múltiples Gestaciones y Complicaciones
```
Paciente con IIG IIP IC -> 2018 3.5 kg / 52 cm, que cursó con preeclampsia; 2020 2.8 kg / 48 cm, que cursó con placenta previa. Menarquía a los 12 años. Refiere ciclos menstruales regulares, sin dismenorrea. Mantiene actividad sexual activa con deseo de fertilidad no logrado.
```

#### Escenario 5: Sin Datos de Menarquía/Sexarquía
```
Paciente con IIG IP. Refiere ciclos menstruales regulares, sin dismenorrea. No mantiene actividad sexual actualmente.
```

#### Escenario 6: Con Dismenorrea Leve
```
Paciente nuligesta. Menarquía a los 13 años. Refiere ciclos menstruales regulares, asociados a dismenorrea de intensidad 3/10.
```

#### Escenario 7: Con Dismenorrea Severa
```
Paciente con IG. Refiere ciclos menstruales regulares, asociados a dismenorrea de intensidad 9/10.
```

#### Escenario 8: Con Método Anticonceptivo
```
Paciente nuligesta. Refiere ciclos menstruales regulares, sin dismenorrea. Utiliza como método anticonceptivo: diu. Mantiene actividad sexual activa sin deseo de fertilidad.
```

#### Escenario 9: Con Control Ginecológico Reciente
```
Paciente con IIG. Refiere ciclos menstruales regulares, sin dismenorrea. Su último control ginecológico fue en octubre del 2024.
```

#### Escenario 10: Con Citología Separada del Control
```
Paciente nuligesta. Refiere ciclos menstruales regulares, sin dismenorrea. Su último control ginecológico fue en septiembre del 2024. Su última citología fue realizada en marzo del 2024.
```

---

### 2. **Examen Funcional** (`summary_functional_exam`)

Función: `_build_functional_exam_summary(user_data)`

#### Escenario 1: Sin Síntomas Funcionales
```
Niega dispareunia. Niega dolor en miembros inferiores durante la menstruación. A nivel gastrointestinal, no refiere síntomas significativos, con una frecuencia evacuatoria de diaria. Sistema urinario sin alteraciones referidas.
```

#### Escenario 2: Con Dispareunia Leve
```
La paciente refiere dispareunia de tipo superficial de leve intensidad (3/10). Niega dolor en miembros inferiores durante la menstruación. A nivel gastrointestinal, no refiere síntomas significativos, con una frecuencia evacuatoria de cada 2 días. Sistema urinario sin alteraciones referidas.
```

#### Escenario 3: Con Dispareunia Severa
```
La paciente refiere dispareunia de tipo profundo de alta intensidad (9/10). Niega dolor en miembros inferiores durante la menstruación. A nivel gastrointestinal, no refiere síntomas significativos, con una frecuencia evacuatoria de diaria. Sistema urinario sin alteraciones referidas.
```

#### Escenario 4: Con Dolor en Miembros Inferiores
```
Niega dispareunia. Presenta dolor en miembros inferiores, descrito como 'punzante' en la zona lateral. A nivel gastrointestinal, no refiere síntomas significativos, con una frecuencia evacuatoria de diaria. Sistema urinario sin alteraciones referidas.
```

#### Escenario 5: Con Síntomas Gastrointestinales
```
Niega dispareunia. Niega dolor en miembros inferiores durante la menstruación. A nivel gastrointestinal, manifiesta síntomas como nauseas, inflamación, dolor al evacuar (disquecia severa (8/10)). Su frecuencia evacuatoria es de cada 3 días. Sistema urinario sin alteraciones referidas.
```

#### Escenario 6: Con Problemas Urinarios
```
Niega dispareunia. Niega dolor en miembros inferiores durante la menstruación. A nivel gastrointestinal, no refiere síntomas significativos, con una frecuencia evacuatoria de diaria. En el sistema urinario, confirma problemas, con dolor al orinar de intensidad moderada (5/10), acompañado de irritación y incontinencia.
```

#### Escenario 7: Con Todos los Síntomas
```
La paciente refiere dispareunia de tipo profundo de moderada intensidad (6/10). Presenta dolor en miembros inferiores, descrito como 'quemante' en la zona posterior. A nivel gastrointestinal, manifiesta síntomas como vomitos, distension, dolor al evacuar (disquecia de máxima intensidad (10/10)). Su frecuencia evacuatoria es de cada 2 días. En el sistema urinario, confirma problemas, con dolor al orinar de intensidad muy alta (8/10), acompañado de nocturia.
```

#### Escenario 8: Con Disquecia Eventual
```
Niega dispareunia. Niega dolor en miembros inferiores durante la menstruación. A nivel gastrointestinal, manifiesta síntomas como dolor al evacuar (disquecia eventual). Su frecuencia evacuatoria es de diaria. Sistema urinario sin alteraciones referidas.
```

---

### 3. **Hábitos Psicobiológicos** (`summary_habits`)

Función: `_build_habits_summary(user_data)`

#### Escenario 1: Sin Actividad Física, Sin Sustancias
```
Niega realizar actividad física de forma regular. En cuanto a hábitos: no fuma, no consume alcohol, y niega el uso de otras sustancias.
```

#### Escenario 2: Con Actividad Física Regular
```
La paciente refiere realizar actividad física regular con una frecuencia de 3 veces por semana, sesiones de 45 minutos, manteniendo este hábito desde hace 6 a 12 meses con el objetivo de mantener un peso saludable. En cuanto a hábitos: no fuma, consume alcohol (Ocasional), y niega el uso de otras sustancias.
```

#### Escenario 3: Fumadora, Sin Alcohol, Sin Sustancias Ilícitas
```
Niega realizar actividad física de forma regular. En cuanto a hábitos: fuma (Sí), no consume alcohol, y niega el uso de otras sustancias.
```

#### Escenario 4: Consume Alcohol Ocasional, Sin Otras Sustancias
```
Niega realizar actividad física de forma regular. En cuanto a hábitos: no fuma, consume alcohol (Ocasional), y niega el uso de otras sustancias.
```

#### Escenario 5: Consume Sustancias Ilícitas
```
Niega realizar actividad física de forma regular. En cuanto a hábitos: no fuma, consume alcohol (Sí), y refiere uso de otras sustancias (Sí).
```

#### Escenario 6: Todos los Hábitos Negativos
```
Niega realizar actividad física de forma regular. En cuanto a hábitos: fuma (Sí), consume alcohol (Sí), y refiere uso de otras sustancias (Sí).
```

#### Escenario 7: Actividad Física con Objetivo Específico
```
La paciente refiere realizar actividad física regular con una frecuencia de 5 veces por semana, sesiones de 60 minutos, manteniendo este hábito desde hace más de un año con el objetivo de mejorar la resistencia cardiovascular. En cuanto a hábitos: no fuma, no consume alcohol, y niega el uso de otras sustancias.
```

#### Escenario 8: Actividad Física Reciente
```
La paciente refiere realizar actividad física regular con una frecuencia de 2 veces por semana, sesiones de 30 minutos, manteniendo este hábito desde hace menos de un mes con el objetivo de perder peso. En cuanto a hábitos: no fuma, consume alcohol (Ocasional), y niega el uso de otras sustancias.
```

---

## 📄 **INFORME MÉDICO RESUMIDO** (Tamaño Carta)

El informe médico resumido usa un **resumen narrativo único** que combina toda la información en un párrafo continuo.

Función: `build_narrative_summary(report_data)`

### Escenario 1: Caso Básico - Control Ginecológico Normal
```
Paciente quien acude a consulta por presentar control ginecológico. Al interrogatorio, manifiesta niega dismenorrea, niega dispareunia, niega disquecia y sin deseo de fertilidad aparente. El ultrasonido transvaginal reporta: Útero ambos ovarios sin patología estructural. Se establece el diagnóstico de Control ginecológico normal. Se indica el siguiente plan:<br/><ul><li>Iniciar Anticonceptivos: Genesa 20 ® tomar 1 comprimido el primer día de la menstruación todos los días a la misma hora durante 28 días. Iniciar la segunda caja el primer día de menstruación del próximo ciclo.</li><li>Prevención vacunación para VPH: Gardasil 4 o Gardasil 9 por 3 dosis</li></ul>
```

### Escenario 2: Con Dismenorrea Moderada
```
Paciente quien acude a consulta por presentar dolor pélvico. Al interrogatorio, manifiesta dismenorrea moderada (5/10), niega dispareunia, niega disquecia y sin deseo de fertilidad aparente. El ultrasonido transvaginal reporta: Útero con miomas pequeños. Se establece el diagnóstico de Dismenorrea funcional. Se indica el siguiente plan:<br/><ul><li>Analgésicos antiinflamatorios durante la menstruación</li><li>Control en 3 meses</li></ul>
```

### Escenario 3: Con Dispareunia Severa
```
Paciente quien acude a consulta por presentar dolor durante las relaciones sexuales. Al interrogatorio, manifiesta niega dismenorrea, dispareunia severa (8/10), niega disquecia y sin deseo de fertilidad aparente. El ultrasonido transvaginal reporta: Endometriosis en ovarios. Se establecen los siguientes diagnósticos:<br/>1) Endometriosis<br/>2) Dispareunia secundaria Se indica el siguiente plan:<br/><ul><li>Tratamiento hormonal</li><li>Fisioterapia del suelo pélvico</li><li>Control en 6 meses</li></ul>
```

### Escenario 4: Con Disquecia de Máxima Intensidad
```
Paciente quien acude a consulta por presentar dolor al evacuar. Al interrogatorio, manifiesta niega dismenorrea, niega dispareunia, disquecia de máxima intensidad (10/10) y sin deseo de fertilidad aparente. El ultrasonido transvaginal reporta: Endometriosis profunda. Se establece el diagnóstico de Endometriosis profunda con afectación rectosigmoidea. Se indica el siguiente plan:<br/><ul><li>Estudio de extensión con resonancia magnética</li><li>Evaluación quirúrgica</li></ul>
```

### Escenario 5: Con Deseo de Fertilidad No Logrado
```
Paciente quien acude a consulta por presentar infertilidad. Al interrogatorio, manifiesta dismenorrea severa (7/10), dispareunia moderada (5/10), niega disquecia y con deseo de fertilidad no logrado. El ultrasonido transvaginal reporta: Quistes endometriósicos bilaterales. Se establecen los siguientes diagnósticos:<br/>1) Endometriosis<br/>2) Infertilidad secundaria Se indica el siguiente plan:<br/><ul><li>Laparoscopia diagnóstica y terapéutica</li><li>Estudio de fertilidad de pareja</li><li>Asesoramiento reproductivo</li></ul>
```

### Escenario 6: Múltiples Síntomas Funcionales
```
Paciente quien acude a consulta por presentar dolor pélvico crónico. Al interrogatorio, manifiesta dismenorrea severa (8/10), dispareunia de alta intensidad (9/10), disquecia severa (7/10) y sin deseo de fertilidad aparente. El ultrasonido transvaginal reporta: Endometriosis extensa con adherencias. Se establecen los siguientes diagnósticos:<br/>1) Endometriosis severa<br/>2) Dolor pélvico crónico<br/>3) Adherencias pélvicas Se indica el siguiente plan:<br/><ul><li>Tratamiento médico con análogos de GnRH</li><li>Laparoscopia quirúrgica</li><li>Manejo multidisciplinario del dolor</li></ul>
```

### Escenario 7: Sin Ultrasonido
```
Paciente quien acude a consulta por presentar irregularidad menstrual. Al interrogatorio, manifiesta niega dismenorrea, niega dispareunia, niega disquecia y sin deseo de fertilidad aparente. Se establece el diagnóstico de Ciclos irregulares. Se indica el siguiente plan:<br/><ul><li>Registro de ciclos menstruales</li><li>Estudio hormonal</li><li>Control en 2 meses</li></ul>
```

### Escenario 8: Diagnóstico Único Simple
```
Paciente quien acude a consulta por presentar flujo vaginal. Al interrogatorio, manifiesta niega dismenorrea, niega dispareunia, niega disquecia y sin deseo de fertilidad aparente. El ultrasonido transvaginal reporta: Sin alteraciones. Se establece el diagnóstico de Vulvovaginitis. Se indica el siguiente plan:<br/><ul><li>Tratamiento antimicótico</li><li>Control en 1 mes</li></ul>
```

### Escenario 9: Plan con Múltiples Viñetas
```
Paciente quien acude a consulta por presentar sangrado intermenstrual. Al interrogatorio, manifiesta dismenorrea moderada (6/10), niega dispareunia, niega disquecia y sin deseo de fertilidad aparente. El ultrasonido transvaginal reporta: Pólipo endometrial. Se establece el diagnóstico de Pólipo endometrial. Se indica el siguiente plan:<br/><ul><li>Histeroscopia diagnóstica y terapéutica</li><li>Biopsia endometrial</li><li>Control post-procedimiento</li><li>Reevaluación en 3 meses</li></ul>
```

### Escenario 10: Sin Plan (Solo Observaciones)
```
Paciente quien acude a consulta por presentar consulta de rutina. Al interrogatorio, manifiesta niega dismenorrea, niega dispareunia, niega disquecia y sin deseo de fertilidad aparente. El ultrasonido transvaginal reporta: Útero y ovarios normales.
```

---

## 📊 **Resumen de Diferencias**

| Aspecto | Historia Médica Completa | Informe Médico Resumido |
|---------|-------------------------|------------------------|
| **Tamaño de papel** | Oficio (Legal) | Carta (Letter) |
| **Estructura** | 3 resúmenes separados en secciones | 1 resumen narrativo único |
| **Contenido** | Detallado, estructurado | Narrativo, fluido |
| **Secciones** | - Antecedentes Obstétricos y Ginecológicos<br>- Examen Funcional<br>- Hábitos psicobiológicos | - Párrafo narrativo único |
| **Uso** | Archivo completo del paciente | Resumen para el paciente |

---

## 🔍 **Notas Técnicas**

1. **Historia Médica Completa**:
   - Usa `summary_gyn_obstetric`, `summary_functional_exam`, `summary_habits`
   - Cada resumen se genera independientemente
   - Se muestran en secciones separadas del PDF

2. **Informe Médico Resumido**:
   - Usa `build_narrative_summary()` que crea un párrafo narrativo único
   - Combina: motivo de consulta, hallazgos funcionales, ultrasonido, diagnóstico y plan
   - El plan se formatea como lista HTML con viñetas

3. **Campos que NO aparecen en el Informe Resumido**:
   - Antecedentes familiares/personales
   - Resumen gineco-obstétrico detallado
   - Hábitos psicobiológicos detallados
   - Examen físico completo

4. **Campos que SÍ aparecen en ambos**:
   - Motivo de consulta (directo en historia, en narrativo en informe)
   - Hallazgos funcionales (resumen en historia, en narrativo en informe)
   - Ultrasonido
   - Diagnóstico
   - Plan
   - Observaciones (solo en historia completa)

