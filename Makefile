# ================================
# Makefile para API Reclamos
# ================================

# Configuración
APP_NAME = reclamos-api
IMAGE_NAME = prj-api-abc-solicitudes_i
CONTAINER_NAME = prj-api-abc-solicitudes_c
PORT = 8101
ENV_FILE = .env

# --------------------------------
# Construir la imagen
# --------------------------------
build:
	@echo "🛠️  Construyendo imagen Docker..."
	docker build -t $(IMAGE_NAME) .

# --------------------------------
# Ejecutar el contenedor
# --------------------------------
run:
	@echo "🚀 Levantando contenedor..."
	docker run -d \
		--name $(CONTAINER_NAME) \
		--env-file $(ENV_FILE) \
		--add-host=host.docker.internal:host-gateway \
		-p $(PORT):$(PORT) \
		$(IMAGE_NAME)

# --------------------------------
# Detener el contenedor
# --------------------------------
stop:
	@echo "🧹 Deteniendo contenedor..."
	-docker stop $(CONTAINER_NAME)
	-docker rm $(CONTAINER_NAME)

# --------------------------------
# Reconstruir imagen y levantar contenedor
# --------------------------------
rebuild: stop build run

# --------------------------------
# Mostrar logs
# --------------------------------
logs:
	docker logs -f $(CONTAINER_NAME)

# --------------------------------
# Entrar al contenedor
# --------------------------------
bash:
	docker exec -it $(CONTAINER_NAME) bash

# --------------------------------
# Limpiar todo (imagen + contenedor)
# --------------------------------
clean:
	@echo "🧽 Eliminando contenedor e imagen..."
	-docker stop $(CONTAINER_NAME)
	-docker rm $(CONTAINER_NAME)
	-docker rmi $(IMAGE_NAME)
