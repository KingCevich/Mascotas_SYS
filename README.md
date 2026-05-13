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

> **Nota:** Requiere que `auth_serv` esté corriendo en el puerto 8001 para validar tokens en operaciones de escritura.
