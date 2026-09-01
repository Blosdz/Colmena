# ¿Qué es "hermes" en este repositorio?

## Resumen

No hay ningún sistema, módulo, servicio o herramienta llamado "Hermes" documentado
o implementado dentro de este proyecto (COLMENA). La única traza del nombre en
todo el repositorio es un directorio y un archivo:

```
_hermes/phase_status.json
```

No existe código, configuración, imports, referencias en `docs/`, en el backend,
en el frontend, ni en el historial de commits que expliquen qué es "Hermes",
quién lo escribe o para qué se usa dentro de este proyecto.

## Contenido real del archivo

```json
{
  "phase_19C": "completed",
  "validated_with_screenshots": true,
  "frontend_build": "passed",
  "next_recommended_phase": "19D_visual_qa_freeze",
  "do_not_start_public_form_yet": true
}
```

Es un JSON plano de 5 campos que parece ser un "checkpoint" de estado de alguna
fase de trabajo (fase `19C`, con una fase siguiente sugerida `19D_visual_qa_freeze`
y una bandera para no empezar todavía el formulario público). No trae timestamp,
autor, ni ningún otro metadato.

## Conclusión

Dentro de este repo, "Hermes" **no es nada identificable**: no hay una arquitectura,
servicio o convención de ese nombre que se pueda documentar. Si "Hermes" es una
herramienta externa (por ejemplo, un orquestador de agentes que use este JSON
como buzón de estado entre fases de desarrollo), su documentación vive fuera de
este repositorio y no hay contexto suficiente aquí para describirla.

Si en el futuro se identifica qué escribe/lee este archivo, este documento debería
actualizarse con esa información.
