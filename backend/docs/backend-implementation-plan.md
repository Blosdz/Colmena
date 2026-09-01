# Plan de implementación del backend

1. **Core y editor — implementado.** Mantener modelos, migración, CRUD,
   edición batch, política de bloqueo, árbol, matriz y clonado con pruebas.
2. **Surveys y captura — implementado con corrección pendiente de verificación
   DB.** Verificar opciones contra el option set, persistir selección múltiple,
   conservar valores canónicos y rechazar cuerpos ambiguos.
3. **Dataset y analítica — implementado en alcance actual.** Completar la
   representación explícita de selecciones múltiples en exports y datasets.
4. **CENSOPAS — implementado en estado provisional.** Incorporar únicamente
   baremos y algoritmos oficiales autorizados; mantener privacidad uniforme.
5. **Seguridad — prioridad alta.** Proteger routers de negocio, derivar el
   propietario del JWT y aplicar autorización central por proyecto/recurso.
6. **Jobs — prioridad alta antes de escalar.** Mover regresiones, clustering,
   reportes y exports pesados a una cola con estados y reintentos.
7. **Formatos pendientes.** Añadir pyreadstat/Polars y pruebas reales para
   SPSS, Power BI y Parquet; añadir un renderer si se requieren PDF/DOCX.
8. **Calidad y migraciones.** Reconstruir el entorno con las versiones de
   Poetry, ejecutar los 92 casos recolectados, validar Alembic contra PostgreSQL
   y crear migraciones incrementales para cada cambio futuro.

## Extensión Likert, baremos y tesis — implementada en `0003`

1. Roles de ítems puntuables/exógenos/descriptivos y secciones públicas.
2. Escalas Likert reutilizables y campos exógenos transaccionales.
3. Baremos multinivel manuales o asistidos, con validación antes de activar.
4. Scoring general 0–100, polaridad, pesos, faltantes configurables y corridas
   inmutables por participante/constructo.
5. Overview y tablas de baremos, normalidad, Spearman con BH y comparación de
   grupos exógenos.
6. Frontend integrado para construir, responder y visualizar estos resultados.
