# E4a – Funcionalidades añadidas en Django

Proyecto: **Streamers United** (grupo IW-BI-04).

## Cómo ponerlo en marcha

```
pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata datos_ejemplo
python manage.py crear_roles
python manage.py createsuperuser
python manage.py runserver
```

`crear_roles` crea los grupos del panel de administración y un usuario de prueba para cada uno (contraseña `Streamers2026`).

Abre http://127.0.0.1:8000/: redirige a `/es/` o a `/en/` según el idioma del navegador.

Para comprobar todas las mejoras automáticamente: `python manage.py test streamers` (25 pruebas).

Para añadir, editar o borrar canales desde la web hay que iniciar sesión (enlace «Iniciar sesión» en la barra lateral) con un usuario que tenga permisos, por ejemplo `admincontenido` o `editor`.

| Opción | Puntos | Estado |
|---|---|---|
| 1. JavaScript / AJAX | 0,50 | ✅ |
| 2. Vistas basadas en clases | 0,50 | ✅ |
| 3. Formularios basados en el modelo | 0,50 | ✅ |
| 4. Admin personalizado con roles | 0,50 | ✅ |
| 5. Datos iniciales | 0,25 | ✅ |
| 6. Multilingüismo (i18n) | 0,50 | ✅ |
| 7. Rendimiento y seguridad | 0,50 | ✅ |
| 8. Despliegue en Render | 0,75 | ⏳ Preparado, falta publicarlo (ver la sección de la opción 8) |

---

## Opción 1: interacción en el cliente con JavaScript y AJAX (0,50)

Archivo: `streamers/static/js/streamers.js` (JavaScript sin librerías, con `fetch`).

| Funcionalidad | Dónde verla | Técnica |
|---|---|---|
| **Búsqueda de canales en vivo** | `/canales/`: escribe en el buscador | Evento `input` con espera de 300 ms → `GET /api/canales/?q=` → JSON → se repintan las tarjetas sin recargar la página. La URL se actualiza con `history.replaceState`. |
| **Botón «Seguir canal»** | Detalle de un canal | `POST /canales/<id>/seguir/` por AJAX con el token CSRF en la cabecera `X-CSRFToken`. Devuelve JSON con los nuevos seguidores. Cada visitante solo puede seguir un canal una vez; después el botón queda en «Siguiendo». |
| **Efectos** | Resultados, contador y mensajes | Las tarjetas aparecen con una animación, el contador «late» al seguir y los mensajes de confirmación se pueden cerrar y desaparecen solos. Se respeta `prefers-reduced-motion`. |

Vistas del servidor: `CanalBusquedaJsonView` y `SeguirCanalView` en `streamers/views.py`.

**Mejora progresiva:** sin JavaScript todo sigue funcionando. El buscador envía el formulario (`?q=`) y la lista se filtra en el servidor; el botón de seguir hace un POST normal y redirige.

## Opción 2: vistas basadas en clases en todas las funcionalidades (0,50)

Todas las vistas de `streamers/views.py` son clases:

- Consulta: `TemplateView`, `ListView`, `DetailView`.
- Formularios: `CreateView`, `UpdateView`, `DeleteView` (con `SuccessMessageMixin`).
- AJAX: `View` con métodos `get` / `post`.

## Opción 3: formularios en la aplicación pública basados en el modelo (0,50)

Archivo: `streamers/forms.py`.

- **`CanalForm`** (ModelForm de `Canal`): crear (`/canales/nuevo/`), editar (`/canales/<id>/editar/`) y borrar con confirmación (`/canales/<id>/borrar/`). Incluye la relación 1:N (categoría) con un desplegable y la N:M (plataformas) con casillas. Validación propia: no se permiten dos canales con el mismo nombre, sin distinguir mayúsculas.
- **`CreadorForm`** (ModelForm de `Creador`): añadir o editar el creador de un canal (relación 1:1). El canal se toma de la URL; si ya tiene creador, «nuevo» redirige a «editar».
- Plantilla común `includes/campos_formulario.html`: pinta cada campo con su etiqueta, su ayuda y sus errores.
- Mensajes de confirmación tras guardar o borrar (framework `messages`).
- Los formularios exigen iniciar sesión y tener el permiso correspondiente (ver la opción 7). Los botones «Editar», «Borrar» y «Añadir» solo aparecen a quien puede usarlos.

## Opción 4: aplicación de administración personalizada con roles (0,50)

**Diseño** (`templates/admin/base_site.html` y `streamers/static/css/admin.css`): cabecera, título y pie propios, con los colores de la web (variables CSS del admin en modo claro).

**Listados y formularios** (`streamers/admin.py`):

- Canales: columnas de plataformas y de «tiene creador», búsqueda por nombre, descripción o creador, filtros, campos agrupados (`fieldsets`), creador editable dentro de la ficha del canal (inline) y acción «Poner a cero los seguidores».
- Categorías y plataformas: columna con el número de canales (ordenable). La ficha de la categoría muestra sus canales.
- Creadores: búsqueda y selector de canal con autocompletado.

**Roles** (comando `python manage.py crear_roles`):

| Grupo | Usuario de prueba | Puede |
|---|---|---|
| Administradores de contenido | `admincontenido` | Todo sobre las 4 entidades; editar seguidores (también desde el listado) y usar la acción de reinicio. |
| Editores | `editor` | Crear y editar canales y creadores; solo ver categorías y plataformas. **No** puede borrar, y los seguidores le aparecen en solo lectura. |
| Revisores | `revisor` | Solo consultar. |

Además de los permisos de Django, el admin cambia según el rol con `get_readonly_fields`, `get_actions` y `list_editable`.

## Opción 5: carga de datos iniciales (0,25)

`streamers/fixtures/datos_ejemplo.json` contiene todas las entidades: 5 categorías, 4 plataformas, 10 canales y 10 creadores. Se carga con `python manage.py loaddata datos_ejemplo`.

## Opción 6: multilingüismo – i18n (0,50)

La web está en **español** (idioma por defecto) y en **inglés**.

- **URLs con idioma** (`iw_bi_04/urls.py`, `i18n_patterns`): `/es/canales/` y `/en/canales/`. Al entrar en `/`, `LocaleMiddleware` redirige al idioma del navegador; si no es ninguno de los dos, al español.
- **Selector de idioma** en la cabecera: formulario que envía a la vista `set_language` de Django y te deja **en la misma página** en el otro idioma.
- **Textos traducidos**: todas las partes estáticas de las plantillas (`{% translate %}` y `{% blocktranslate %}`, con plurales: «1 canal / 2 canales» → «1 channel / 2 channels»), etiquetas y errores de los formularios, mensajes de confirmación y textos propios del panel de administración (`gettext_lazy`). Los mensajes propios de Django (por ejemplo «Este campo es obligatorio») ya vienen traducidos.
- **JavaScript multilingüe**: el JavaScript no lleva textos escritos dentro; los recibe ya traducidos desde la plantilla en atributos `data-txt-*`.
- **Traducciones**: `locale/en/LC_MESSAGES/django.po` (texto, 103 cadenas) y `django.mo` (compilado, el que usa Django). Si se añaden textos nuevos: `python manage.py makemessages -l en`, traducir el `.po` y `python manage.py compilemessages` (en Windows hace falta instalar *gettext*).
- Configuración en `settings.py`: `LANGUAGES`, `LOCALE_PATHS` y `LocaleMiddleware`.

Los nombres y descripciones de canales, categorías y plataformas son datos de la base de datos, así que no se traducen (la tarea pide traducir las partes estáticas).

## Opción 7: rendimiento y seguridad (0,50)

**Rendimiento**: se eliminan las consultas repetidas (problema N+1).

| Página | Antes | Ahora |
|---|---|---|
| Portada | 1 consulta por categoría + 1 por canal destacado | 1 consulta |
| Categorías / Plataformas | 1 consulta por elemento para contar canales | 1 consulta (`annotate(Count)`) |
| Canales | — | 1 consulta (`select_related`) |
| Detalles | 1 consulta por relación | `select_related` / `prefetch_related` |

Las pruebas `RendimientoTests` comprueban el número de consultas con `assertNumQueries`. También se reutiliza la conexión a la base de datos (`conn_max_age`) y, en producción (solo con `DEBUG=False`; en desarrollo los sirve `runserver`), WhiteNoise sirve los estáticos comprimidos y con el hash en el nombre (`style.19f0d4161d6b.css`), para que el navegador los guarde en caché.

**Seguridad**: análisis con tres herramientas.

1. `python manage.py check --deploy`: **8 avisos antes → 0 después**. Se corrigió así:
   - `SECRET_KEY`, `DEBUG` y `ALLOWED_HOSTS` se leen de variables de entorno (`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`). En desarrollo se usan los valores de siempre.
   - En producción (`DEBUG=False`): redirección a HTTPS, HSTS y cookies de sesión y CSRF solo por HTTPS.
   - Siempre: `X_FRAME_OPTIONS = 'DENY'`, `nosniff`, `Referrer-Policy`, `Cross-Origin-Opener-Policy` y cookies `HttpOnly`.
   - Correo por consola solo en desarrollo; SMTP en producción.
2. `bandit` (análisis estático del código Python): sin problemas.
3. `pip-audit` (vulnerabilidades conocidas en dependencias): ninguna en Django 6.1.1.

Otras medidas en el código:
- El JavaScript inserta los datos con `textContent`, nunca con `innerHTML`, para evitar XSS.
- Las acciones que modifican datos solo aceptan POST con token CSRF (comprobado en las pruebas).
- La suma de seguidores se hace con `F()` en la base de datos para no perder clics simultáneos.
- **Formularios públicos protegidos**: crear, editar y borrar canales y creadores exige iniciar sesión (`/es/cuentas/entrar/`) y tener el permiso de Django correspondiente (`PermissionRequiredMixin`). Son los mismos permisos que dan los roles de `crear_roles`: el editor crea y edita pero no borra, el revisor no puede modificar nada y sin sesión se redirige al inicio de sesión. Cerrar sesión solo se puede hacer por POST.
- **Seguidores**: en el formulario público solo los administradores de contenido pueden escribir el número de seguidores, igual que en el admin.
- **Botón «Seguir»**: cada visitante suma como mucho un seguidor por canal (se recuerda en su sesión), para que no se puedan inflar las cifras a base de clics.

Para comprobar la configuración de producción:
```
set DJANGO_DEBUG=False
set DJANGO_SECRET_KEY=una-clave-larga-y-aleatoria-de-mas-de-50-caracteres
set DJANGO_ALLOWED_HOSTS=localhost
python manage.py check --deploy
```

## Opción 8: despliegue en Render (0,75)

El proyecto está preparado para desplegarse en Render y se ha probado simulando el despliegue: los mismos comandos de construcción, `gunicorn`, `DEBUG=False` y HTTPS detrás de un proxy.

Archivos añadidos o cambiados:
- `render.yaml`: *Blueprint* de Render. Define el servicio web, los comandos de construcción y arranque, y las variables de entorno. La `SECRET_KEY` la genera Render.
- `requirements.txt`: `gunicorn` (servidor de producción), `whitenoise` (archivos estáticos), `dj-database-url` y `psycopg` (para usar PostgreSQL si se quiere).
- `settings.py`: `WhiteNoiseMiddleware`, `STATIC_ROOT`, almacenamiento de estáticos comprimido, base de datos desde `DATABASE_URL` (SQLite si no existe) y `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` automáticos con `RENDER_EXTERNAL_HOSTNAME`.

En cada despliegue, Render ejecuta: `pip install` → `collectstatic` → `migrate` → `loaddata datos_ejemplo` → `crear_roles` → `createsuperuser` (con las variables `DJANGO_SUPERUSER_*`).

### Pasos para desplegar

1. Subir el proyecto a GitHub (con `render.yaml` en la raíz del repositorio).
2. Crear una cuenta en https://render.com con GitHub.
3. **New → Blueprint**, elegir el repositorio y pulsar **Connect**.
4. Render pedirá dos valores: `DJANGO_SUPERUSER_PASSWORD` (contraseña del usuario `admin`) y `DEMO_PASSWORD` (de `admincontenido`, `editor` y `revisor`; si se deja vacío, `Streamers2026`).
5. **Apply**. A los pocos minutos la web queda en `https://streamers-united.onrender.com` (o el nombre que asigne Render).

En el plan gratuito, la base de datos SQLite se vuelve a crear con los datos de ejemplo en cada despliegue. Los cambios que se hagan en la web publicada se pierden al reiniciarse el servicio. Para conservarlos, se crea una base PostgreSQL en Render y se añade su `DATABASE_URL` al servicio; el código ya la usa sin más cambios.

URL del despliegue: *(añadir aquí cuando esté publicado)*

---

**Validación HTML:** todas las páginas públicas, en los dos idiomas y también las de errores de formulario y las de mensajes, pasan el validador de la W3C sin errores.
