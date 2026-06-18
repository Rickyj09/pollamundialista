# Auditoría del Proyecto Flask: Polla Mundialista

## Resumen ejecutivo

El workspace `C:\Ricardo\paginas_web\polla_mundialista` **sí corresponde a la aplicación Polla Mundialista**.

No encontré referencias textuales a:

- `DojoManager`
- `Baekjul`
- `Ayala`
- `Ayalatkd`
- `Club Apolo`
- `Academia`
- `Alumno`
- `Instructor`
- `Sucursal`
- `Torneo`
- `Participacion`

Además:

- `flask routes` ejecutado dentro de este directorio expone la ruta `/resultados/general`
- la ruta `/` está registrada como `public.home`
- la plantilla principal usa el título `Polla Mundialista`
- el `create_app()` registrado en este proyecto monta únicamente blueprints de la Polla

Conclusión preliminar:

**No hay evidencia de contaminación de código DojoManager dentro de este repositorio.**

La causa raíz más probable es que, en la ejecución donde viste `BAEKJUL AYALA GYM / DojoManager`, **no se estaba sirviendo este proyecto**, sino otra aplicación distinta o un proceso Flask diferente.

---

## 1. Aplicación que arranca realmente en este proyecto

### Archivo revisado

- `app/__init__.py`

### Resultado

`create_app()` registra exactamente estos blueprints:

- `public`
- `auth`
- `admin`
- `jornadas`
- `apuestas`
- `resultados`

### Registro actual en `create_app()`

```python
app.register_blueprint(public_bp)
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(jornadas_bp, url_prefix="/jornadas")
app.register_blueprint(apuestas_bp, url_prefix="/apuestas")
app.register_blueprint(resultados_bp, url_prefix="/resultados")
```

### Página principal real

La ruta `/` apunta a:

- endpoint: `public.home`
- blueprint: `public`
- template: `app/templates/public/home.html`

### Evidencia

`app/blueprints/public/routes.py`

```python
@public_bp.route("/")
def home():
    return render_template("public/home.html")
```

La plantilla `app/templates/public/home.html` muestra:

- título: `Inicio`
- contenido: `Polla Mundialista`

La plantilla base `app/templates/base.html` también contiene:

- título por defecto: `Polla Mundialista`
- encabezado: `Polla Mundialista`

---

## 2. Búsqueda de referencias a DojoManager y términos ajenos

### Consulta usada

```text
DojoManager
Baekjul
Ayala
Ayalatkd
Club Apolo
Academia
Alumno
Instructor
Sucursal
Torneo
Participacion
```

### Resultado

No se encontraron coincidencias dentro del workspace actual.

### Conclusión

No hay strings, nombres de dominio funcional, vistas ni modelos que apunten a DojoManager dentro de este proyecto.

---

## 3. Verificación de blueprints esperados

### Blueprints esperados para Polla Mundialista

- `apuestas`
- `resultados`
- `jornadas`
- `admin`
- `auth`

### Estado

Todos existen y todos están registrados en `create_app()`.

### Directorios encontrados

- `app/blueprints/admin`
- `app/blueprints/apuestas`
- `app/blueprints/auth`
- `app/blueprints/jornadas`
- `app/blueprints/public`
- `app/blueprints/resultados`

---

## 4. Rutas Flask registradas realmente

### Fuente

`app.url_map` generado desde este mismo proyecto.

### Rutas encontradas

| Ruta | Endpoint | Métodos |
|---|---|---|
| `/` | `public.home` | `GET` |
| `/admin/` | `admin.dashboard` | `GET` |
| `/admin/apuestas/registrar-por-usuario` | `admin.registrar_apuesta_por_usuario` | `GET, POST` |
| `/admin/jornadas` | `admin.listar_jornadas` | `GET` |
| `/admin/jornadas/<int:jornada_id>` | `admin.detalle_jornada` | `GET` |
| `/admin/pagos` | `admin.listar_pagos` | `GET` |
| `/admin/pagos/<int:pago_id>/confirmar` | `admin.confirmar_pago` | `GET` |
| `/admin/pagos/nuevo` | `admin.nuevo_pago` | `GET, POST` |
| `/admin/partidos` | `admin.listar_partidos` | `GET` |
| `/admin/partidos/<int:partido_id>/resultado` | `admin.ingresar_resultado` | `GET, POST` |
| `/admin/ranking/recalcular` | `admin.recalcular_rankings` | `POST` |
| `/admin/usuarios` | `admin.listar_usuarios` | `GET` |
| `/admin/usuarios/nuevo` | `admin.nuevo_usuario` | `GET, POST` |
| `/apuestas/` | `apuestas.mis_apuestas` | `GET` |
| `/apuestas/actualizar/<int:apuesta_id>` | `apuestas.actualizar_apuesta` | `POST` |
| `/apuestas/editar/<int:apuesta_id>` | `apuestas.editar_apuesta` | `GET` |
| `/apuestas/guardar/<int:jornada_id>` | `apuestas.guardar_apuesta` | `POST` |
| `/apuestas/nueva/<int:jornada_id>` | `apuestas.nueva_apuesta` | `GET` |
| `/auth/login` | `auth.login` | `GET, POST` |
| `/auth/logout` | `auth.logout` | `GET` |
| `/auth/register` | `auth.register` | `GET, POST` |
| `/jornadas/` | `jornadas.listar` | `GET` |
| `/jornadas/<int:jornada_id>` | `jornadas.detalle` | `GET` |
| `/resultados/` | `resultados.tabla` | `GET` |
| `/resultados/general` | `resultados.ranking_general` | `GET` |
| `/static/<path:filename>` | `static` | `GET` |

### Hallazgo importante

La ruta:

- `/resultados/general`

**sí existe** en la aplicación cargada desde este proyecto.

Si en navegador devuelve `404`, entonces la app que estaba atendiendo la petición **no era esta**.

---

## 5. Verificación de templates

### `templates/base.html`

Existe:

- `app/templates/base.html`

Contiene branding de:

- `Polla Mundialista`

### `templates/index.html`

No existe `app/templates/index.html`.

### Ruta `/`

La ruta `/` usa:

- `app/templates/public/home.html`

No usa `index.html`.

### Conclusión

La home real de este proyecto no tiene relación con DojoManager.

---

## 6. Modelos detectados

### Modelos claramente pertenecientes a Polla Mundialista

- `usuario.py`
- `grupo.py`
- `equipo.py`
- `jornada_grupo.py`
- `partido.py`
- `apuesta.py`
- `pronostico.py`
- `pago_jornada.py`
- `acumulado.py`
- `auditoria_apuesta_admin.py`

### Modelos sospechosos o ajenos

No encontré modelos con semántica de:

- dojo
- alumnos
- instructores
- sucursales
- torneos

### Conclusión

La capa de modelos del workspace es consistente con Polla Mundialista.

---

## 7. Archivos sospechosos o fuera de lugar

### Dentro del código del proyecto

No encontré archivos que apunten claramente a DojoManager.

### Observaciones menores

Sí existen algunas variantes de templates con nombres antiguos o paralelos:

- `app/templates/auth/login.html`
- `app/templates/auth/login_v2.html`
- `app/templates/auth/register_v2.html`
- `app/templates/apuestas/nueva.html`
- `app/templates/apuestas/nueva_v2.html`
- `app/templates/apuestas/editar.html`
- `app/templates/apuestas/editar_v2.html`
- `app/templates/resultados/general.html`
- `app/templates/resultados/general_v2.html`
- `app/templates/resultados/tabla.html`
- `app/templates/resultados/tabla_v2.html`
- `app/templates/jornadas/listar.html`
- `app/templates/jornadas/listar_v2.html`

Esto no indica contaminación externa, pero sí sugiere que el proyecto tiene **versiones coexistentes de vistas** y conviene consolidarlas después.

---

## 8. Evidencia sobre el problema real

### Import real del módulo `app`

Comprobado con Python dentro de este directorio:

- `app.__file__ = C:\Ricardo\paginas_web\polla_mundialista\app\__init__.py`

Esto confirma que `import app` en este workspace resuelve al paquete correcto.

### Variable `FLASK_APP`

Variables observadas:

- `FLASK_APP=` vacío
- `FLASK_ENV=` vacío
- `PYTHONPATH=` vacío

### CLI `flask`

El comando `flask` actualmente resuelve a:

- `C:\Users\User\AppData\Local\Programs\Python\Python311\Scripts\flask.exe`

### Verificación de CLI real

Tanto estos comandos dentro del directorio actual:

- `flask routes`
- `flask --app app routes`
- `python -m flask routes`

devuelven la misma aplicación y muestran `/resultados/general`.

### Diagnóstico técnico

Con la evidencia actual, el problema más probable es uno de estos:

1. Se estaba ejecutando `flask run` desde otro directorio distinto al de `polla_mundialista`.
2. Ya había otro proceso escuchando en `127.0.0.1:5000`.
3. El navegador estaba apuntando a una instancia previa de otra app.
4. Se estaba lanzando otra app Flask desde otra terminal o perfil de entorno.

No hay evidencia de mezcla de código DojoManager dentro de este repo.

---

## 9. Causa raíz más probable

### Hipótesis principal

**La aplicación equivocada se estaba sirviendo en el puerto consultado, no este código.**

### Motivos

- El branding del repo es `Polla Mundialista`.
- La home registrada es `public.home`.
- `/resultados/general` sí existe.
- No hay strings ni modelos de DojoManager.
- `flask routes` dentro de este directorio devuelve solo endpoints de la Polla.

---

## 10. Plan de corrección propuesto

### Fase 1: asegurar ejecución correcta

1. Ejecutar explícitamente la app correcta:

```powershell
flask --app app run
```

o:

```powershell
python -m flask --app app run
```

2. Confirmar el directorio antes de arrancar:

```powershell
pwd
```

Debe ser:

```text
C:\Ricardo\paginas_web\polla_mundialista
```

3. Verificar qué proceso ocupa el puerto 5000 antes de abrir navegador.

4. Si hay otra app en `5000`, correr esta en otro puerto temporal:

```powershell
flask --app app run --port 5001
```

### Fase 2: endurecer el arranque del proyecto

Recomendaciones para dejarlo menos ambiguo:

1. Crear un archivo raíz `wsgi.py` o `run.py` en el directorio del proyecto.
2. Arrancar siempre con `--app app` o `--app wsgi`.
3. Documentar el comando oficial de arranque en `README.md`.
4. Opcional: renombrar el paquete genérico `app` a algo menos ambiguo en el futuro.

---

## 11. Qué archivos eliminar o corregir después de la auditoría

### Eliminar

Por ahora:

- **ninguno por contaminación DojoManager**

No hay evidencia suficiente para borrar archivos por mezcla de proyectos.

### Consolidar más adelante

Conviene revisar y posiblemente consolidar:

- templates duplicados `*_v2` vs plantillas antiguas
- vistas no usadas como `general.html`, `tabla.html`, `nueva.html`, `editar.html`, `listar.html`

Pero esto sería una tarea de limpieza interna de Polla, no de desinfección DojoManager.

---

## 12. Estado final de la auditoría

### Diagnóstico

El proyecto actual **sí es Polla Mundialista**.

### Causa raíz

La evidencia apunta a un **problema de ejecución/entorno/proceso activo**, no a contaminación del repositorio.

### Archivos sospechosos

- No se detectaron archivos pertenecientes a DojoManager dentro del repo.

### Rutas registradas

- Sí incluyen `/resultados/general`

### Blueprints registrados

- `public`
- `auth`
- `admin`
- `jornadas`
- `apuestas`
- `resultados`

### Próximo paso recomendado

Validar el arranque con:

```powershell
python -m flask --app app run --port 5001
```

y comprobar en navegador:

- `http://127.0.0.1:5001/`
- `http://127.0.0.1:5001/resultados/general`

Si ahí aparece Polla Mundialista, queda confirmado que el problema estaba en la instancia servida en `5000`, no en este código.
