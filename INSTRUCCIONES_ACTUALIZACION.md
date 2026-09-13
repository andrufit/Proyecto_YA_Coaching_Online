# Actualización Y&A: interfaz responsive y recuperación de contraseña

## Qué incluye

- Menú lateral negro y dorado con el logo original, navegación por rol y buscador de secciones.
- Resumen con datos reales: peso registrado, días/comidas del plan y perfil; para entrenadores y administradores, recuentos de clientes.
- Pestañas del entrenador para perfil, entrenamiento y nutrición. Los editores permanecen montados al cambiar entre esas pestañas.
- Menú móvil, cierre con Escape, recorrido del foco, botones y formularios adaptados.
- Recuperación de contraseña mediante SMTP: enlace de 20 minutos, uso único y hash SHA-256 en base de datos. Contraseñas con el mecanismo Argon2 existente. Al restablecer, se invalidan los JWT anteriores de esa cuenta.
- Protección de solicitudes por cuenta: no se genera otro enlace durante dos minutos. La respuesta no indica si existe el correo; el envío se ejecuta después de responder.

El diseño reproduce la identidad y estructura de la referencia. No incluye métricas ficticias de calorías/adherencia, biblioteca de ejercicios, suscripciones ni notificaciones que aún no existen en el backend.

## 1. Conservar la versión actual

Detén React y Uvicorn con Ctrl+C. Copia tu carpeta actual a una ubicación de respaldo antes de reemplazar archivos. Guarda también tus cambios pendientes en Git local si corresponde.

No borres la carpeta original, sus archivos .env, el entorno virtual ni .git. El ZIP no contiene tus secretos ni tu historial Git.

Antes de aplicar la migración puedes crear un respaldo PostgreSQL desde la raíz del proyecto:

```powershell
docker compose exec db pg_dump -U ya_coaching_user -d ya_coaching -Fc -f /tmp/ya_antes_interfaz.dump
docker compose cp db:/tmp/ya_antes_interfaz.dump .\ya_antes_interfaz.dump
```

Comprueba que los dos comandos terminen correctamente y que el archivo local exista. Adapta usuario y nombre de base si los cambiaste. No ejecutes `docker compose down -v`.

## 2. Copiar la actualización

Extrae el ZIP en una carpeta temporal. Copia el contenido de `Proyecto_YA_Coaching_Online/backend` sobre `backend` de tu proyecto y el de `frontend` sobre `frontend`. Acepta reemplazar los archivos coincidentes. Es una combinación de carpetas: no elimines las carpetas de destino.

Conserva tus archivos `.env` existentes. El logo viene incluido en `frontend/public/logo-ya.png`.

## 3. Aplicar la migración

En una terminal dentro de `backend`, con el entorno virtual activo:

```powershell
python -m alembic current
python -m alembic upgrade head
python -m alembic current
python -m alembic check
python -m pytest -q
```

La nueva revisión es `a813b72c9e10`, posterior a `4c8f5dc31622` (nutrición). Añade `users.auth_version` y `password_resets`; no elimina usuarios, asignaciones ni planes. No generes otra migración para este cambio.

## 4. Configurar el correo

Agrega a tu `backend/.env`, sin borrar las variables existentes:

```dotenv
SMTP_HOST=servidor_smtp_de_tu_proveedor
SMTP_PORT=587
SMTP_SECURITY=starttls
SMTP_USERNAME=tu_usuario_smtp
SMTP_PASSWORD=tu_credencial_smtp
SMTP_FROM=correo_remitente_verificado
PASSWORD_RESET_MINUTES=20
```

Utiliza los valores reales que entregue tu proveedor. Para TLS implícito usa `SMTP_SECURITY=ssl` y el puerto que indique el proveedor (habitualmente 465). No compartas las credenciales en el chat ni las agregues a Git. Esta actualización no requiere enviármelas.

`FRONTEND_URL` debe ser la dirección exacta donde el usuario abre React: en local, por ejemplo `http://localhost:5173`. En un despliegue debe ser la URL pública HTTPS. El correo contiene un enlace a esa dirección; localhost solo sirve en el computador donde corre el frontend.

Reinicia Uvicorn tras cambiar `.env`. Si el correo no está configurado, el formulario informa que la recuperación todavía no está disponible. El envío SMTP real no se verificó porque no se proporcionó una cuenta de correo. Las pruebas automatizadas sustituyen el envío por un buzón de prueba.

Si el proveedor rechaza el envío, la API conserva una respuesta genérica para no revelar cuentas; consulta el registro del backend (`Password recovery email delivery failed`) y revisa remitente/credenciales. Se elimina el enlace fallido para permitir reintentar. La tarea de correo corre en el proceso del servidor: no es una cola persistente con reintentos. Para un despliegue público a mayor escala, añadir cola y límites por IP en el proxy.

## 5. Ejecutar frontend y backend

Terminal backend:

```powershell
python -m uvicorn app.main:app --reload
```

Otra terminal en `frontend`:

```powershell
npm ci
npm run lint
npm run build
npm run dev
```

Abre la dirección que indique Vite. Si cambió de puerto, revisa `FRONTEND_URL` antes de probar recuperación.

## 6. Comprobación en tu computador

1. Cliente: abrir resumen, entrenamiento, nutrición y perfil. Los datos deben coincidir con su cuenta.
2. Entrenador: abrir Clientes, seleccionar cliente y usar las tres pestañas. Editar un plan, guardar y recargar.
3. Administrador: comprobar creación de entrenador y asignación de clientes.
4. Celular: abrir/cerrar menú y revisar formularios y tablas. Las tablas anchas pueden desplazarse dentro de su contenedor.
5. En el acceso, usar «¿Olvidaste tu contraseña?». Recibir el correo real, abrir el enlace y guardar una nueva contraseña.
6. Confirmar que la contraseña anterior ya no permite entrar, que la nueva funciona y que reutilizar el enlace falla.

Guarda los formularios antes de cambiar de cliente, de sección principal o cerrar sesión; esas acciones desmontan los editores. Las pestañas internas del entrenador conservan sus borradores mientras no cambies de cliente.

## Validación de esta entrega

- Suite backend: 126 pruebas aprobadas en Python 3.12/Linux, con dos advertencias de dependencias (httpx/Starlette y anyio). Incluye las 120 pruebas existentes y seis nuevas de recuperación.
- Frontend: compilación TypeScript + Vite y análisis oxlint.
- Migración: SQL generado con dialecto PostgreSQL; no se ejecutó contra tu base real.
- Interfaz: comprobación en navegador con respuestas de API de prueba; no representa datos reales de tus usuarios.
- Tu entorno es Windows/Python 3.14. Ejecuta los comandos anteriores para validar allí. Se mantuvo tu requirements.txt y package-lock.json; el cambio de backend usa dependencias existentes y biblioteca estándar.

## Guardar en Git local

Después de comprobar los flujos:

```powershell
git status
git add backend/app backend/alembic/versions/a813b72c9e10_password_recovery.py backend/tests/test_password_recovery.py backend/.env.example frontend/src frontend/public/logo-ya.png INSTRUCCIONES_ACTUALIZACION.md
git diff --cached --stat
git commit -m "Redisenar interfaz responsive y agregar recuperacion de contrasena"
```

Copia este documento también a la raíz del proyecto si vas a incluirlo en el commit. No añadas el archivo de respaldo de la base de datos a Git.
