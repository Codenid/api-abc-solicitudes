# api-abc-solicitudes
Gestión de Solicitudes


## Pasos

Paso A:

	1. Crear proyecto poetry
		poetry new api-abc-solicitudes

Paso A:

	1. Descargar versión de python
		pyenv install 3.10.14
	2. Activar versión python
		pyenv local 3.10.14

Paso B:

	1. Especificando dependencias
        poetry add fastapi psycopg2-binary pydantic python-dotenv sqlalchemy uvicorn

Paso C:

	1. Creación del entorno
		poetry env use python
	2. Instalar dependencias
		poetry install --no-root

Paso D:

    1. Ejecutar api
        poetry run uvicorn src.api_abc_solicitudes.main:app --reload --port 8101