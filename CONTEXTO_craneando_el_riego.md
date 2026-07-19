# CONTEXTO — Proyecto "Craneando el Riego"

## Qué es
Plataforma de recomendación de riego de precisión para cultivos extensivos (arranca con maíz bajo pivote) en Entre Ríos, Argentina. Integra balance hídrico + sensor de humedad + pronóstico climático para recomendar fecha y lámina de riego, anticipando el cruce del umbral de estrés con 48-72h de margen.

**Frase de posicionamiento:** "El Excel simula, el sensor mide, la calculadora calcula. Craneando el Riego decide: integra los tres, anticipa el riego 72h antes del estrés."

**Problema real que resuelve (confirmado por el agrónomo de campo):** en la campaña 2025-26 hubo estrés hídrico por *lentitud en la toma de decisión de riego*, no por falta de modelo. El sistema ataca eso directamente: anticipar la decisión, no reemplazar el criterio agronómico.

## Equipo
- **Darío** (yo) — desarrollo, método, arquitectura. Sin conocimiento de campo directo.
- **Mariano** — ingeniero agrónomo, acceso operativo y técnico diario al lote piloto (San Martín). Aporta datos de suelo, Kc, criterio agronómico. Es quien tiene el balance hídrico histórico en Excel.
- **Mauricio** — ingeniero agrónomo, rol de interlocución/gestión (contacto con productor, acceso a sensores). Su rol se está reajustando porque el piloto cambió de lote (ver abajo) y él estaba más asociado al lote anterior.

## Decisión de lote piloto — IMPORTANTE, cambió
- Se arrancó asumiendo **El Trébol** (100 ha, maíz, pivote SGR) porque había un Excel de balance hídrico histórico de esa campaña 2025-26.
- **Mariano corrigió: el piloto real debe ser San Martín**, porque él tiene acceso operativo y técnico diario ahí (mejor observabilidad y feedback loop).
- El Excel de El Trébol sigue siendo valioso como *modelo de referencia* (estructura de cálculo, curva Kc, umbrales) pero los datos de suelo específicos de San Martín todavía no están cargados — Mariano los está buscando.
- Kc: Mariano confirmó que van a reusar la misma curva Kc de El Trébol para San Martín (mismo cultivo, misma región).

## Datos técnicos ya disponibles (de El Trébol, sirven de modelo/referencia)

**Suelo (3 horizontes):**
| Horizonte | CC (%) | PMP (%) | DA (g/cm³) | Espesor (dm) |
|---|---|---|---|---|
| 0–20 cm | 25.7 | 14.8 | 1.31 | 2 |
| 20–40 cm | 22.6 | 15.1 | 1.35 | 2 |
| 40–80 cm | 31.3 | 19.8 | 1.40 | 6 |

Agua Útil total: 145.4 mm | Factor ajuste: 0.75 | AU corregida: 109 mm | Techo sistema: 120 mm

**Curva Kc por etapa fenológica (a reusar para San Martín):**
- Emergencia: 0.05–0.09
- Inicial: 0.14–0.25
- Crecimiento: 0.28–0.84
- Desarrollo/Panojamiento-Crítico (pico): 0.96–1.10
- Madurez fisiológica: 0.95 → 0.56

**Umbral de riego por etapa (referencia El Trébol, a confirmar si aplica igual a San Martín):**
- Inicial/Crecimiento: 60 mm de AU
- Desarrollo-PC (etapa crítica): 72 mm de AU

**Lluvia efectiva por rango:**
| Rango PP (mm) | Coeficiente |
|---|---|
| < 15 | 1.00 |
| 15–30 | 0.85 |
| 30–60 | 0.70 |
| > 60 | 0.55 |

**Fuente ETP histórica:** campañas 2014-15/2015-16, Hidráulica ER Urdinarrain.

**Fuentes meteo locales confirmadas por Mariano (mejores que NASA POWER como primaria):**
- Estación Hidráulica de la Provincia, Urdinarrain
- Estación Bolsa de Cereales, Urdinarrain
- Estación Concepción del Uruguay (también válida)
- NASA POWER queda como fallback, no primaria.

**Archivo fuente:** `Balance_hidrico_-_Maiz_-_El_Trebol.xlsx` (hoja "ET - SGR" tiene el balance día a día completo con fórmulas; útil para replicar la lógica exacta del motor).

## Reglas de negocio / lógica agronómica confirmadas por Mariano

1. **Riego óptimo por default**, con un parámetro configurable de "% de CC a cubrir": 100% = estrategia ofensiva (asegura rendimiento), 85-90% = conservadora (deja margen para lluvia). **Este parámetro tiene que ser configurable en el dashboard, no hardcodeado.**

2. **Lámina de riego NO es fija.** La fórmula debe ser: `lámina recomendada = MIN(lámina para llevar a % CC objetivo, capacidad de infiltración del suelo)`. Mariano prefiere láminas altas por eficiencia, pero el techo real es la infiltración. **Falta el dato de tasa de infiltración de San Martín — Mariano dijo que hay un análisis archivado, lo está buscando.**

3. **Kc por cultivo, no híper-variable.** En la práctica agronómica se usa un Kc por cultivo (con ajustes gruesos por latitud/ciclo). Decisión tomada: usar la curva tabulada de El Trébol para maíz en San Martín, dejar el código parametrizable pero NO poblar variantes por latitud/ciclo hasta v2 (más lotes, más datos).

4. **Deficit de la campaña pasada:** confirmado como clima excepcional + lentitud en la decisión de riego (hubo problemas mecánicos que retrasaron la ejecución). No fue error del modelo de balance.

## Acceso a datos de sensor (AGSENSE / Valley) — PENDIENTE BLOQUEANTE

- Mauricio tenía originalmente el rol de gestionar esto; ahora Mariano dijo que tiene acceso a la app.
- Existe una cuenta "madre" (probablemente administradora/compartida) — **instrucción explícita: no tocarla ni resetearla, no compartir credenciales de esa cuenta ni de ninguna por chat.**
- **Todavía sin resolver:** si hay API real, exportación CSV, o solo vista de app mobile sin export. Esto es lo más urgente para no frenar Fase 1 (ingesta de datos de humedad real).
- Hay capturas de la app de Valley/AGSENSE (humedad %, voltaje batería, presión PSI, ángulo de pivote) — están disponibles como referencia de qué datos expone la plataforma, pero no confirman mecanismo de acceso programático.

## Geometría / otros datos en camino
- Mariano va a pasar KMZ de campo/pivots (para geometría del lote, útil a futuro para consultas satelitales NDVI/humedad remota).
- Mariano va a pasar info de otros lotes también (mencionado en el doc, sin detalle aún).

## Alcance del MVP — CERRADO Y ACORDADO

**Adentro:**
- Motor de balance hídrico diario automatizado (replica la lógica del Excel de El Trébol)
- Ingesta: sensor de humedad + fuente meteo local (Urdinarrain/Concepción, NASA POWER fallback) + pronóstico 7 días
- Recomendación de fecha próxima de riego + lámina (mm, limitada por infiltración) + tiempo de riego (h, según caudal pivote)
- Dashboard web (Streamlit) con estado hídrico, proyección 7 días, historial riegos aplicados vs recomendados, parámetro configurable de % CC objetivo (conservador/ofensivo)
- Alerta Telegram cuando la proyección cruza umbral (48-72h de anticipación)

**Afuera (backlog v2, explícitamente fuera de los primeros 3 meses):**
- Simulación de rendimiento
- Simulación/optimización económica
- Fertirriego
- Mapa de cárcavas
- Integración automática con pivote (API Valley)
- Multi-lote, multi-cultivo
- Componentes de IA/machine learning (sin datos históricos suficientes todavía — se evalúa después de 1-2 campañas)
- Integraciones con terceros / alianzas externas (ej. contacto de Alemania mencionado por Mauricio, otras plataformas)
- Variantes de Kc por latitud/ciclo de cultivo

**Usuario objetivo confirmado:** el asesor agrónomo (Mariano), no el productor directamente. El productor ejecuta, el agrónomo decide/configura.

**Métrica de éxito propuesta (sin objeción hasta ahora):** reducir a cero (o minimizar) los días con déficit severo de AU en etapa crítica, comparado contra la campaña de referencia.

## Cronograma acordado
- Fase 0 (definiciones + datos de suelo San Martín + resolución acceso sensor): 2 semanas
- Fase 1 (motor de balance + ingesta): 4 semanas
- Fase 2 (recomendación + alertas): 2 semanas
- Fase 3 (dashboard): 3 semanas
- Meta: sistema operativo antes del arranque de campaña 2026-27

## Ritmo de trabajo del equipo
- Reunión semanal de 45 min, día/hora fijos
- Links a otras plataformas (Rindeplus, Winbox, Kilimo) → documento aparte de benchmarks, se revisan al cierre del MVP
- Ideas nuevas durante desarrollo → backlog v2, no se discuten hasta que el MVP funcione
- Cambios de alcance dentro del MVP requieren acuerdo de los tres

## Antecedente crítico: Kilimo ya operó en San Martín (2020-21)

Mariano pasó un informe real de Kilimo (`San_Martin_de_Tours_MAIZ_2021.md`), campaña de maíz 2020-21, en el mismo lote piloto. No es un competidor abstracto — es un proveedor que **ya trabajó ahí y fue reemplazado**.

**Por qué se fue Kilimo (confirmado por el equipo):** creció demasiado como empresa y dejó de lado a este productor. No fue por mal producto — fue por pérdida de foco/atención al cliente chico a medida que escalaban.

**Expectativa del productor (confirmada):** quiere "lo mismo [que Kilimo] y más" — no arranca de cero, arranca comparando contra un estándar ya visto y experimentado. Esto es una espada de doble filo:
- A favor: el productor ya sabe que quiere esta categoría de herramienta, no hay que convencerlo del concepto.
- En contra: el MVP recortado (balance por lote, sin segmentación espacial) puede *parecer* un paso atrás si no se comunica bien el roadmap. Hay que mostrarle explícitamente el plan de fases antes de que la brecha lo sorprenda.

**Ángulo de venta clave:** no competir en cantidad de features contra Kilimo — competir en cercanía y foco. Kilimo lo perdió por escalar; el equipo (Mariano con acceso diario al lote, desarrollo a medida) ofrece exactamente lo que Kilimo dejó de dar.

**Contenido del informe de Kilimo (referencia visual, sin datos numéricos extraíbles — es PDF/imágenes con OCR):**
- Gráfico de Agua Útil (%) vs umbral (%) + riego + precipitaciones, serie oct 2020–mar 2021, por Equipo de pivote (Equipo 1, Equipo 2) y por sección/posición.
- Curva de Kc graficada (oct–mar).
- ETo, ETc, ETc ajustado graficados juntos.
- Balance hídrico acumulado (barras: evapotranspiración, lluvias, riegos, agua útil inicial) como egresos vs ingresos, cierre de campaña.
- **Mapas de humedad del suelo por sección de pivote** (escala 0.0–1.0), tomados cada ~5-10 días toda la campaña — esto es más granular que el enfoque actual (balance único por lote). Candidato fuerte para v2: segmentación espacial dentro del lote/pivote.

**Preguntas pendientes para Mariano/Mauricio sobre esto:**
1. ¿Hay datos crudos detrás del informe, o solo queda el PDF final?
2. Confirmar con el productor si compara activamente contra la experiencia de Kilimo, para calibrar cómo se presenta el roadmap de fases.

## Kc vía NDVI (aporte de Mauricio) — evaluado, incorporado como validación cruzada, no como reemplazo

Mauricio trajo una fórmula de Kc basado en NDVI satelital (GEE):
- Maíz/Trigo: `Kc = 1.44 × NDVI − 0.1`
- Soja: `Kc = 1.36 × NDVI − 0.1`
- `ETc = ETo × Kc`

**Verificado:** es una fórmula real de la literatura de teledetección agrícola (línea de trabajo tipo González-Piqueras/Calera, usada en proyectos como IRRIMAPS en España), validada para cultivos herbáceos incluyendo maíz. No la inventó el equipo, es un aporte técnico legítimo.

**Limitaciones técnicas a tener en cuenta:**
- Es un **Kc basal (Kcb)** — estima la transpiración del canopeo, no incluye evaporación directa de suelo desnudo. El Kc de la planilla de Mariano (tipo FAO-56, 0.05–1.10) sí incluye ese componente. Mezclarlos sin ajuste subestima la ETc en etapas tempranas (suelo desnudo, mucha evaporación directa).
- La literatura reporta R² ~0.7 en el ajuste lineal, con sobreestimación en etapa inicial y subestimación en etapa final respecto a FAO-56. No es "más preciso" per se, es una fuente distinta.

**Decisión de arquitectura:** el motor v1 usa el Kc de tabla (planilla de Mariano) como fuente primaria. El Kc-NDVI vía GEE corre en paralelo como segunda fuente para validación cruzada semanal — sirve para detectar cuándo el cultivo real se desvía de la curva teórica (estrés, crecimiento distinto al esperado), no para reemplazar el cálculo base. Ya existe infraestructura GEE reusable de otros proyectos de Darío (VigorDAE, COVIO), así que el costo de sumar esto es bajo.

## Riesgo de cronograma: datos de suelo San Martín demorados

Van dos rondas de seguimiento sin que aparezcan las constantes hídricas (CC, PMP) de San Martín — Mariano las pidió a un laboratorio externo que todavía no respondió. Es una dependencia de terceros fuera de control del equipo.

**Mitigación propuesta:** arrancar el desarrollo del motor usando los valores de suelo de El Trébol como placeholder temporal (misma lógica de código, se reemplazan las constantes apenas lleguen los datos reales de San Martín). Evita bloquear Fase 1 por un tercero.

## Estado técnico del desarrollo (al 14/07/2026) — motor validado end-to-end

El código en Claude Code (`C:\Users\sdari\Desktop\RIEGO`) avanzó más rápido que los datos reales del lote. Resumen:

**✅ Motor de balance hídrico (`core/balance.py`, `core/soil.py`, `core/crop.py`) — VALIDADO**
- Test unitario (`scratch/test_balance.py`) corre las 152 filas de la campaña de referencia (El Trébol 2025-26) de forma recursiva real: el AU de cada día se retroalimenta del propio resultado del motor en Python, no de las celdas del Excel. El Kc también se calcula 100% en Python (no se lee del Excel), y se contrasta contra el original solo para verificación.
- Resultado: 0.0000 mm de desviación en `AU: Riego` y `AU: Secano` en toda la serie, con recursión y Kc totalmente independientes del Excel.
- **Bug detectado y corregido durante la validación:** las transiciones de nombre de etapa fenológica/umbral (60mm↔72mm) en el Excel de Mariano estaban en fechas de calendario fijas que no coincidían exactamente con los saltos de Kc (que interpolan por DAS). Esto generaba un desfase de pocos días donde el AU calculaba perfecto pero la etapa/umbral asignado podía ser el incorrecto (bug silencioso: no se ve en el número de AU, sí afecta qué umbral de alerta dispara).
  - **Origen real del bug:** inconsistencia en la propia planilla de Mariano (cambia etapa/umbral por fecha de calendario, no por el mismo criterio que genera los saltos de Kc). No fue error de transcripción del equipo de desarrollo. Vale la pena comentárselo a Mariano en algún momento — no para "corregirlo" (ya resuelto en el motor), sino porque es información útil sobre cómo se maneja el criterio en la práctica.
  - **Solución:** se desacoplaron en `core/config.py` dos tablas independientes indexadas por DAS: `KC_DAS_TABLE` (saltos de Kc) y `STAGE_DAS_TABLE` (nombre de etapa + umbral absoluto). `crop.py` las consulta por separado (`get_kc_and_stage()`, `get_umbral_mm()`).
  - Test re-corrido tras el fix: coincidencia 100% en AU, Kc **y** etiqueta de etapa/umbral en las 152 filas.

**✅ Panel de calibración sensor-vs-modelo**
- `core/soil.py` tiene un método único `calculate_au_from_vwc(vwc_list)` que convierte humedad volumétrica (%VWC) a mm de AU. Tanto la curva del modelo (azul) como la curva del sensor (verde, actualmente simulada) llaman a esta misma función — evita diferencias artificiales entre "modelo" y "sensor" que en realidad serían solo bugs de conversión duplicada.
- `data/sensor.py` tiene la interfaz `get_humidity_data(lote, fecha_desde, fecha_hasta) -> pd.DataFrame` como stub con la firma que va a usar el conector real de AGSENSE cuando se resuelva el acceso. El día que haya API/CSV real, el cambio queda acotado a la lógica interna de esa función, sin tocar el resto del sistema.

**✅ Dashboard (`app.py`)** — 7 paneles: configuración agronómica (suelo, siembra, %CC objetivo, infiltración, caudal pivote), semáforo de recomendación (verde/amarillo/rojo con anticipación 48-72h), gráfico central de AU con proyección 7 días y curva de secano, balance acumulado estilo Kilimo, calibración sensor-vs-modelo, validación cruzada Kc teórico vs Kc-NDVI (marcado como stub simulado), alerta Telegram simulada con botón de prueba, y sección de roadmap de fases para manejar expectativa vs Kilimo.
- Corregido: el gráfico de secano ya no se describe como estimador de "rendimiento" (kg/ha) — solo como comparación de disponibilidad de agua en el suelo, para no prometer algo que el sistema no calcula.
- Corregido: el "Simulador Temporal" está etiquetado explícitamente como "Modo Demo — Campaña El Trébol 2025-26" con advertencia de que los parámetros de San Martín se aplicarán cuando lleguen del laboratorio.

**⏳ Pendiente de terceros, no de desarrollo:**
- Constantes de suelo (CC, PMP, DA) y capacidad de infiltración de San Martín — laboratorio externo, sin respuesta todavía.
- Acceso real a datos de AGSENSE (API vs CSV vs solo app) — sin resolver, pero ya no bloquea el desarrollo gracias a la interfaz stub.
- Devolución de Mauricio sobre puntos 4-5 del documento de cierre de ideas (rutina de decisión diaria para especificar el dashboard, rol de usuario).

## Actualización crítica: AGSENSE NO sirve para balance hídrico (18/07/2026)

Mariano aclaró por audio, de forma definitiva: **AGSENSE/Valley es una app de monitoreo operativo del pivote** (encendido/apagado, dirección, presión de agua, velocidad, caudal, amperaje de la bomba) — **no de humedad de suelo para cálculo de balance**. Los sensores de humedad que tenían instalados los desactivaron porque daban datos erráticos/poco confiables.

**Esto cambia el estado del pendiente "acceso a AGSENSE":** no es un acceso por resolver, es una fuente que **no aplica** para lo que se necesitaba. Se retira de la lista de bloqueantes.

**Sensores nuevos en prueba esta campaña (sin fecha de disponibilidad confirmada):**
- Barra con sensor de humedad cada 10 cm.
- Barra de 60 cm con sensor cada 20 cm.
- Todavía no están disponibles — no planificar el MVP asumiendo que van a estar listos. El panel de calibración sensor-vs-modelo sigue corriendo con datos simulados; la interfaz stub (`get_humidity_data()`) ya está lista para conectarlos si llegan a estar disponibles durante el desarrollo.

## Nueva fuente de datos climáticos confirmada y verificada: Estación Urdinarrain (DGHyOS, Entre Ríos)

Mariano pasó el link de la estación meteorológica automática oficial de la Provincia de Entre Ríos: `https://www.hidraulica.gob.ar/ema.php?station=urdinarrain`

**Verificado directamente (fetch):** es una estación real, pública, con secciones específicas de Precipitación, Evapotranspiración, Humedad de Suelo, Temperatura de Suelo, Temperatura, Viento, Presión Barométrica, etc. Tiene reportes descargables en texto plano (formato NOAA: informe semanal, mes actual, mes anterior, año actual, año anterior) y un histórico mensual/anual que se remonta a 2006. Es apta para integración programática (parseo de archivos .txt con URLs estables).

**Hallazgo importante:** esta estación tiene su propia sección de **Humedad de Suelo**, independiente de AGSENSE. No es del lote San Martín específicamente (es de la estación, no del campo), pero es una fuente real y pública que puede servir como segunda referencia mientras no haya sensor propio en el lote.

**Advertencia operativa de Mariano:** la estación viene "complicada el último mes con las baterías" (posibles huecos de datos recientes). Su sugerencia: si una estación falla, tomar el dato de la más cercana funcional (ej. Concepción del Uruguay como alternativa a Urdinarrain).

**Segunda fuente de precipitación:** Bolsa de Cereales — `https://www.bolsacer.org.ar/site/precipitaciones/`

**Pendiente técnico:** actualizar `data/weather.py` para usar estas fuentes reales (Urdinarrain + Bolsa de Cereales) como primarias, con NASA POWER como fallback, y lógica de fallback entre estaciones si una está caída/con huecos de datos.

## Confirmación de la fórmula de balance por parte de Mariano (coincide con lo ya implementado)

Mariano confirmó explícitamente la lógica: nivel de agua inicial (agua útil, estimado con muestras secadas a estufa) + clima diario → `AU = Precipitación + Riego − Evapotranspiración (ETo × Kc)` diario. Coincide exactamente con lo que ya está implementado en `core/balance.py`. Sin cambios necesarios ahí.

## Punto de agenda pendiente para la próxima reunión (pedido explícito de Mariano)

Mariano marcó como "clave" el panel de **Validación Cruzada Kc Teórico vs Kc-NDVI** del dashboard, y dijo que en la próxima reunión quiere explicar **por qué hay tanta diferencia en el mercado entre los distintos balances hídricos de distintos proveedores** — probablemente vinculado a qué Kc o qué fuente satelital usa cada uno. Vale la pena dejarlo como punto fijo de agenda: es conocimiento de campo que Mariano tiene y que puede afinar la lógica del sistema. Mejor tratarlo en la reunión con el dashboard corriendo en vivo que por chat.

Mauricio, en paralelo, preguntó si había que definir "parámetros de cálculo y límites para que dispare alertas" — pregunta correcta y relacionada, mejor responderla también en la reunión mostrando el semáforo (verde/amarillo/rojo) ya implementado.

## Infiltración de suelo — sin dato de campo, se usa estimado por bibliografía (vertisol)

Mariano confirmó que San Martín es un **vertisol** y que no hay dato de infiltración medido en campo — solo rango bibliográfico. Es razonable: los vertisoles no tienen un valor fijo (se agrietan en seco, permitiendo infiltración rápida inicial; al humedecerse la arcilla se hincha y sella las grietas, bajando fuerte la tasa sostenida).

**Decisión provisoria:** usar un valor conservador (el extremo bajo del rango bibliográfico para suelos arcillosos pesados, orden de 2-15 mm/h de tasa sostenida) como parámetro en `config.py`, etiquetado explícitamente como "estimado por bibliografía, no medido en campo — pendiente de ensayo de infiltrómetro si se justifica más adelante". Reemplazable sin tocar el resto del código, mismo criterio que el resto de los datos placeholder.

## Pendientes activos (al 18/07/2026)
1. Mariano: datos de suelo (CC, PMP, DA por horizonte) de San Martín — dueño del campo los pasa el lunes 20/07, apenas vuelva de trabajo con hacienda
2. ~~Resolver mecanismo de acceso a datos del sensor AGSENSE~~ — RESUELTO (negativo): AGSENSE no sirve para humedad de suelo, solo monitoreo operativo del pivote. Retirado como bloqueante.
3. Mauricio: todavía no devolvió su parte del documento de cierre de ideas (puntos 4 y 5)
4. Confirmar con Mauricio su rol reajustado ahora que el piloto es San Martín y no El Trébol
5. Preguntar a Mariano si existen datos crudos detrás del informe de Kilimo, o si solo queda el PDF
6. Preparar cómo comunicar al productor el roadmap de fases (MVP recortado vs expectativa "igual o más que Kilimo")
7. Decidir con Mariano cómo conviven el Kc de tabla y el Kc-NDVI — vinculado al punto que Mariano quiere explicar en la próxima reunión (por qué difieren los balances comerciales del mercado)
8. Actualizar `data/weather.py` para usar Estación Urdinarrain + Bolsa de Cereales como fuentes primarias reales (con fallback a estación más cercana si hay huecos), NASA POWER como fallback secundario
9. Evaluar si la sección "Humedad de Suelo" de la estación Urdinarrain sirve como segunda referencia para el panel de calibración
10. Confirmar si los sensores nuevos en prueba esta campaña (barra 10cm / barra 60cm cada 20cm) llegan a estar disponibles a tiempo — sin fecha confirmada, no depender de esto para el MVP
11. Responder a Mauricio en la próxima reunión (no por chat) sobre parámetros y límites de disparo de alertas, mostrando el semáforo ya implementado
12. Cargar en `config.py` el valor de infiltración estimado por bibliografía para vertisol (provisorio, etiquetado como no medido en campo)

## Archivos disponibles en la carpeta de trabajo
- `Balance_hidrico_-_Maiz_-_El_Trebol.xlsx` — balance hídrico histórico completo, campaña 2025-26, El Trébol. Hoja clave: "ET - SGR" (día a día con fórmulas de Kc, ETC, AU, umbral).
- Documento "Craneando el Riego — Cierre de Etapa de Ideas v1.0" con devolución de Mariano incorporada (línea por línea).
- Capturas de la app AGSENSE365/Valley (humedad, batería, presión, ángulo de pivote) — referencia visual únicamente; confirmado que esta app es solo monitoreo operativo del pivote, no fuente de humedad de suelo para balance.
- Links de referencia de mercado: winbox.cl/calculadora-riego, winbox.cl/calculadora-aforo, rindeplus.com (Mariano identifica Rindeplus como el competidor que más integra funciones similares).
- `San_Martin_de_Tours_MAIZ_2021.md` — informe de cierre de campaña de Kilimo en el lote piloto actual (2020-21). Solo gráficos/imágenes (sin datos numéricos extraíbles), pero referencia de alcance de producto y de la experiencia previa del productor con un proveedor comercial.
- Audio `AGSENSE.ogg` (transcripto) — Mariano explica en detalle el rol real de AGSENSE (solo operativo), confirma la fórmula de balance, y pasa los links de fuentes climáticas reales (Urdinarrain, Bolsa de Cereales).

## Notas de tono/estilo del equipo
- Mariano responde corto, técnico, directo — buena señal de compromiso, no hay que sobre-explicarle.
- Mauricio tiende a traer referencias externas (links, contactos) que hay que contener sin desestimarlo — se le da rol de "benchmarks + gestión operativa" para canalizar eso.
- El documento de cierre de ideas se diseñó a propósito en formato "sé / asumo / necesito que definan" para no imponer decisiones agronómicas sobre gente de campo — funcionó bien, mantuvo ese formato en próximas iteraciones si hace falta actualizar el doc.
