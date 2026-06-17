# 🐶 mascotas_serv

Microservicio de reportes del sistema SanosYSalvos. Gestiona los reportes de mascotas perdidas y encontradas, junto con la información de contacto asociada a cada reporte. Las operaciones de escritura requieren autenticación JWT con rol Admin.

**Puerto:** `8002`

---

## Responsabilidades

- Crear y gestionar reportes de mascotas perdidas o encontradas
- Almacenar datos de geolocalización del reporte (latitud/longitud)
- Gestionar contactos asociados a cada reporte
- Validar tokens JWT en operaciones de escritura comunicándose con `auth_serv`

---

## Modelos

### `Reporte`
Representa un reporte de mascota perdida o encontrada.

| Campo | Tipo | Descripción |
|---|---|---|
| `tipo_reporte` | CharField | Tipo de reporte: `Perdido` o `Encontrado` |
| `nombre_mascota` | CharField | Nombre de la mascota |
| `raza` | CharField | Raza de la mascota |
| `color` | CharField | Color de la mascota |
| `tamano` | DecimalField | Tamaño en kg |
| `fech_perdida` | DateField | Fecha del incidente |
| `hora_perdida` | TimeField | Hora del incidente |
| `latitud` | DecimalField | Latitud de donde se vio la mascota |
| `longitud` | DecimalField | Longitud de donde se vio la mascota |
| `descripcion` | TextField | Descripción adicional |
| `estado_reporte` | CharField | Estado: `Activo` o `Resuelto` |

### `Contacto`
Información de contacto vinculada a un reporte.

| Campo | Tipo | Descripción |
|---|---|---|
| `reporte` | ForeignKey | Reporte al que pertenece el contacto |
| `telefono` | CharField | Teléfono de contacto |
| `email` | CharField | Email de contacto |
| `whatsapp_enable` | BooleanField | Si acepta contacto por WhatsApp |

---

## Endpoints

| Método | URL | Auth requerida | Descripción |
|---|---|---|---|
| GET | `/api/reportes/` | No | Listar todos los reportes |
| POST | `/api/reportes/` | Sí (Admin) | Crear un nuevo reporte |
| GET | `/api/reportes/{id}/` | No | Obtener un reporte por ID |
| PATCH | `/api/reportes/{id}/` | Sí (Admin) | Actualizar un reporte |
| DELETE | `/api/reportes/{id}/` | Sí (Admin) | Eliminar un reporte |
| GET | `/api/contactos/` | No | Listar todos los contactos |
| POST | `/api/contactos/` | Sí (Admin) | Crear un nuevo contacto |
| GET | `/api/contactos/{id}/` | No | Obtener un contacto por ID |
| PATCH | `/api/contactos/{id}/` | Sí (Admin) | Actualizar un contacto |
| DELETE | `/api/contactos/{id}/` | Sí (Admin) | Eliminar un contacto |

> **Nota:** Se puede utilizar Thunder o Postman para las peticiones API por medio http://127.0.0.1:8002/.
---

## Motor de IA y coincidencias
 
### Arquitectura del flujo asíncrono
 
```
Frontend / Postman
       │
       ▼
  bff_serv (8003)
       │  multipart/form-data con foto
       ▼
 mascotas_serv (8002)
       │
       ├─► Guarda reporte en BD (responde 201 inmediato)
       │
       └─► Celery encola tarea analizar_reporte_async
                   │
                   ▼
            FastAPI IA (8006)
            MobileNetV2 → vector 1280 dims + similitudes
                   │
                   ├─► Guarda vector en Reporte.foto_vector
                   ├─► Calcula score combinado (65% visual + 35% textual)
                   └─► notificaciones_serv (8005)
                       POST /api/notificaciones/enviar/
                       tipo_evento: ia_completada
```
 
### Score de coincidencia
 
El score final combina dos dimensiones:
 
| Componente | Peso | Descripción |
|---|---|---|
| Score visual | 65% | Similitud coseno entre vectores MobileNetV2 |
| Score textual | 35% | Coincidencia de raza, color, tamaño y ubicación |
 
Solo se notifican coincidencias con `score_final >= 40.0`.
 
---
 
## Entorno virtual separado para IA
 
El microservicio FastAPI de IA requiere un entorno virtual **independiente** del entorno principal del proyecto, debido a que TensorFlow y sus dependencias son incompatibles con algunas versiones de Python y con las librerías del resto de microservicios.
 
### Crear el entorno de IA
 
```bash
# Desde la raíz del proyecto
cd mascotas_serv
 
# Crear entorno virtual con Python 3.10 o 3.11 (TensorFlow no soporta 3.12+)
python3.10 -m venv venv_ia
 
# Activar el entorno
# Windows:
venv_ia\Scripts\activate
# Linux/Mac:
source venv_ia/bin/activate
```
 
### Instalar dependencias de IA
 
```bash
pip install fastapi uvicorn tensorflow numpy pillow scikit-learn requests
```
 
### Dependencias principales del entorno IA
 
| Librería | Versión recomendada | Uso |
|---|---|---|
| `fastapi` | ≥0.100 | Framework API REST |
| `uvicorn` | ≥0.23 | Servidor ASGI |
| `tensorflow` | 2.13–2.15 | MobileNetV2 para extracción de vectores |
| `numpy` | ≥1.24 | Operaciones vectoriales |
| `pillow` | ≥9.0 | Procesamiento de imágenes |
| `scikit-learn` | ≥1.3 | Similitud coseno |
| `requests` | ≥2.28 | Llamadas HTTP internas |
 
### Levantar el microservicio IA
 
```bash
# Con el entorno venv_ia activado
cd fastapi_ia
uvicorn main:app --host 0.0.0.0 --port 8006 --reload
```
 
---
 
## Redis y Celery
 
### Redis (broker de tareas)
 
Redis actúa como intermediario entre mascotas_serv y el worker de Celery. Debe estar corriendo antes de iniciar el worker.
 
```bash
# Levantar Redis con Docker
docker run -d -p 6379:6379 --name redis redis
 
# Verificar que está corriendo
docker ps
```
 
> Si ya tienes un contenedor Redis creado previamente, usa `docker start redis` en vez de `docker run`.
 
### Celery worker
 
El worker de Celery procesa las tareas de análisis IA en segundo plano. Debe ejecutarse desde el directorio de `mascotas_serv` con el entorno principal activado (no el de IA).
 
```bash
# Con el entorno sys_venv activado
cd mascotas_serv
 
# Windows (requiere --pool=solo por limitaciones de Windows)
celery -A mascotas_serv worker --loglevel=info --pool=solo
 
# Linux/Mac
celery -A mascotas_serv worker --loglevel=info
```
 
### Verificar que todo está activo
 
Antes de crear reportes con foto, confirmar que los siguientes servicios están corriendo:
 
| Servicio | Puerto | Cómo verificar |
|---|---|---|
| Redis | 6379 | `docker ps` → estado `Up` |
| Celery worker | — | Terminal muestra `celery@... ready.` |
| FastAPI IA | 8006 | `GET http://127.0.0.1:8006/` → `{"status": "ok"}` |
| mascotas_serv | 8002 | `GET http://127.0.0.1:8002/api/reportes/` → 200 |
 
---
 
## Tests


Los tests de escritura usan `@patch` para simular la validación del token JWT con `auth_serv`.

**Tests de modelos:**
- `test_create_reporte` — Verifica la creación de un reporte con todos sus campos
- `test_create_contacto` — Verifica la creación de un contacto vinculado a un reporte

**Tests de API:**
- `test_list_reportes` — GET devuelve lista de reportes (status 200)
- `test_create_reporte` — POST con token válido crea un reporte (status 201)
- `test_retrieve_reporte` — GET por ID devuelve el reporte correcto
- `test_update_reporte` — PATCH con token Admin actualiza el estado del reporte
- `test_delete_reporte` — DELETE con token Admin elimina el reporte
- `test_list_contactos` — GET devuelve lista de contactos (status 200)
- `test_create_contacto` — POST con token válido crea un contacto
- `test_retrieve_contacto` — GET por ID devuelve el contacto correcto
- `test_update_contacto` — PATCH con token Admin actualiza el teléfono
- `test_delete_contacto` — DELETE con token Admin elimina el contacto

```bash
cd mascotas_serv
python manage.py test
```

---

## Levantar el servicio

```bash
cd mascotas_serv
python manage.py migrate
python manage.py runserver 8002
```

> **Nota:** Requiere que `auth_serv` esté corriendo en el puerto 8001 para validar tokens en operaciones de escritura. Para el flujo completo con IA, también deben estar activos Redis, el worker de Celery, el microservicio FastAPI IA en el puerto 8006, y `notificaciones_serv` en el puerto 8005.
