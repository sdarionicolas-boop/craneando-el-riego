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

## Pendientes activos (al 10/07/2026)
1. Mariano: datos de suelo (CC, PMP, DA por horizonte) de San Martín — en curso
2. Mariano: tasa de infiltración de San Martín (análisis archivado que va a buscar) — en curso
3. Resolver mecanismo de acceso a datos del sensor (API vs CSV vs solo app) — bloqueante para Fase 1, sin dueño claro todavía
4. Mauricio: todavía no devolvió su parte del documento de cierre de ideas (puntos 4 y 5, específicamente su lectura del rol de usuario y su rutina de decisión para el dashboard)
5. Confirmar con Mauricio su rol reajustado ahora que el piloto es San Martín y no El Trébol (él estaba más asociado al lote anterior)
6. Definir responsable operativo del acceso al sensor ahora que cambió el contexto (originalmente era Mauricio)

## Archivos disponibles en la carpeta de trabajo
- `Balance_hidrico_-_Maiz_-_El_Trebol.xlsx` — balance hídrico histórico completo, campaña 2025-26, El Trébol. Hoja clave: "ET - SGR" (día a día con fórmulas de Kc, ETC, AU, umbral).
- Documento "Craneando el Riego — Cierre de Etapa de Ideas v1.0" con devolución de Mariano incorporada (línea por línea).
- Capturas de la app AGSENSE365/Valley (humedad, batería, presión, ángulo de pivote) — referencia visual, sin acceso programático confirmado.
- Links de referencia de mercado: winbox.cl/calculadora-riego, winbox.cl/calculadora-aforo, rindeplus.com (Mariano identifica Rindeplus como el competidor que más integra funciones similares).

## Notas de tono/estilo del equipo
- Mariano responde corto, técnico, directo — buena señal de compromiso, no hay que sobre-explicarle.
- Mauricio tiende a traer referencias externas (links, contactos) que hay que contener sin desestimarlo — se le da rol de "benchmarks + gestión operativa" para canalizar eso.
- El documento de cierre de ideas se diseñó a propósito en formato "sé / asumo / necesito que definan" para no imponer decisiones agronómicas sobre gente de campo — funcionó bien, mantuvo ese formato en próximas iteraciones si hace falta actualizar el doc.
