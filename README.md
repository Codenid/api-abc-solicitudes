# api-abc-solicitudes
Gestión de Solicitudes


## Pasos

Paso A:

	1. Crear proyecto poetry
		poetry new api-abc-solicitudes

Paso B:

	1. Descargar versión de python
		pyenv install 3.10.14
	2. Activar versión python
		pyenv local 3.10.14

Paso B:

	1. Especificando dependencias
        poetry add fastapi psycopg2-binary pydantic python-dotenv sqlalchemy uvicorn

Paso D:

	1. Creación del entorno
		poetry env use python
	2. Instalar dependencias
		poetry install --no-root

Paso E:

    1. Ejecutar api
        poetry run uvicorn src.api_abc_solicitudes.main:app --reload --port 8101

Paso F:

	1. Generar requirements.txt fuera del contenedor
		poetry export -f requirements.txt --without-hashes > requirements.txt

Paso G:

	1. Crear imagen
		docker build -t prj-api-abc-solicitudes_i .
	2. Ejecutar contenedor
		docker run -d --name prj-api-abc-solicitudes_c -p 8101:8101 --env-file .env prj-api-abc-solicitudes_i

## Nuevo Esquema:

reclamos-api/
└─ app/
   ├─ __init__.py
   ├─ main.py
   ├─ db.py
   ├─ models.py
   ├─ schemas.py
   └─ routers/
      ├─ __init__.py
      └─ reclamos.py
.env.example

## Usar Makefile

### Construir imagen
make build

### Levantar contenedor
make run

### Ver logs en tiempo real
make logs

### Detener contenedor
make stop

### Reconstruir desde cero y ejecutar
make rebuild

### Entrar a la shell del contenedor
make bash

### Borrar todo (contenedor + imagen)
make clean
