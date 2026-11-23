# Infraestructura containerizada con balanceo de carga y monitoreo en Docker
Proyecto final – Implementación de Infraestructura Containerizada con Balanceo de Cargas y Monitoreo en Docker (Universidad Autónoma de Occidente).

**Autor:** Juan Esteban Dominguez Quijano

## Descripción
Infraestructura de microservicios orquestada con Docker Compose:

- **Nginx** como proxy inverso y balanceador de carga (Round Robin) hacia **3 instancias** de un backend en Python/Flask.
- Cada backend se identifica en su respuesta y expone `/metrics` con `prometheus_client`.
- **Prometheus** recolecta métricas de los backends, de Nginx (vía *Nginx Prometheus Exporter*) y de **cAdvisor**.
- **Grafana** visualiza las métricas con un dashboard que se carga automáticamente (provisionamiento).
- Todos los servicios se comunican por una red Docker personalizada (`monitor_net`).

## Estructura del repositorio
Proyecto Final-Sistemas Operativos/
├── backend/
│   ├── app.py                 # Aplicación Flask con métricas Prometheus
│   ├── requirements.txt       # Dependencias necesarias
│   └── Dockerfile             # Imagen del servicio backend
├── nginx/
│   └── nginx.conf             # Proxy inverso, balanceo y stub_status
├── prometheus/
│   └── prometheus.yml         # Targets y frecuencia de scraping
├── grafana/
│   ├── provisioning/          # Datasource y proveedor de dashboards
│   └── dashboards/infra.json  # Dashboard de monitoreo
├── docs/                      # Capturas y PDF del informe
├── docker-compose.yml         # Servicios, red y volúmenes
├── load_test.js               # Prueba de carga con k6
└── README.md

## Requisitos previos
- Docker Engine 20.10+ y Docker Compose v2 (o Docker Desktop).
- [k6](https://k6.io/docs/get-started/installation/) para las pruebas de carga.
  - Windows: `winget install k6 --source winget`
  - Ubuntu/Debian:
    bash
    sudo gpg -k
    sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
      --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
    echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" \
      | sudo tee /etc/apt/sources.list.d/k6.list
    sudo apt-get update && sudo apt-get install k6
- Git.
- Puertos libres en el host: **80**, **9090** y **3000**.

## Cómo levantar la infraestructura
bash
git clone https://github.com/juanestdominguez/Proyecto-Final-Sistemas-Operativos.git
cd Proyecto-Final-Sistemas-Operativos
docker compose up -d --build
docker compose ps
Deben quedar **8 contenedores** en ejecución: `backend1`, `backend2`, `backend3`, `nginx-proxy`, `nginx-exporter`, `cadvisor`, `prometheus` y `grafana`. Los backends tardan unos segundos en pasar a *healthy*; Nginx arranca cuando los tres lo están.

## URLs de acceso
Servicio           | URL                   | Notas                           
Aplicación (Nginx) | http://localhost      | Balanceada entre los 3 backends
Prometheus         | http://localhost:9090 | Estado de targets en `/targets`
Grafana            | http://localhost:3000 | Usuario `admin` / contraseña `admin`; el dashboard ya viene cargado

## Verificación

### 1. Balanceo de carga
Linux / macOS / Git Bash:
bash
for i in {1..6}; do curl -s http://localhost; echo; done

Windows (PowerShell):
1..6 | ForEach-Object { (Invoke-RestMethod http://localhost).instancia }

Resultado esperado: el campo `instancia` alterna entre `Backend-Instancia-1`, `-2` y `-3`. También se puede ver qué backend respondió en la cabecera `X-Backend`:
bash
curl -si http://localhost | grep -i x-backend

### 2. Targets de Prometheus
En http://localhost:9090/targets deben aparecer en estado **UP**: `backend_instances` (3), `nginx_exporter` (1), `cadvisor` (1) y `prometheus` (1).

### 3. Dashboard de Grafana
Abra http://localhost:3000, inicie sesión y entre al dashboard **Infraestructura Docker - Monitoreo**. El datasource de Prometheus y el dashboard se cargan solos desde `grafana/`. 
Paneles incluidos: tasa de solicitudes, latencia promedio y p95 por instancia, conexiones activas de Nginx, CPU y memoria por servicio, CPU/memoria/disco/red agregados de Docker (cAdvisor) y distribución porcentual de solicitudes por instancia.

## Pruebas de carga con k6
`load_test.js` ejecuta 60 s: rampa hasta 50 usuarios virtuales (15 s), **meseta de 50 usuarios (30 s)** y descenso a 0 (15 s). Define umbrales: menos de 1 % de errores y p95 < 200 ms.

bash
k6 run load_test.js

Sin instalar k6 (usando Docker):

powershell
# Windows PowerShell
Get-Content load_test.js | docker run --rm -i -e BASE_URL=http://host.docker.internal grafana/k6 run -

bash
# Linux
docker run --rm -i --add-host=host.docker.internal:host-gateway \
  -e BASE_URL=http://host.docker.internal grafana/k6 run - < load_test.js

Mientras corre la prueba, observe el dashboard con rango *Last 15 minutes* y refresco de 5 s: se verá la tasa de solicitudes repartida entre las tres instancias, el aumento de conexiones activas en Nginx y el consumo de CPU.

## Notas y limitaciones
- En **Docker Desktop (Windows/WSL2)**, cAdvisor expone las métricas de CPU, memoria, disco y red a nivel de cgroup agregado (`/docker`, `/`), no por contenedor. Por eso el consumo por servicio del dashboard se obtiene de las métricas de proceso (`process_cpu_seconds_total`, `process_resident_memory_bytes`) que expone cada servicio.
- El backend usa el servidor de desarrollo de Flask; es suficiente para la prueba, pero en producción se usaría un servidor WSGI como Gunicorn.

## Detener y limpiar
bash
docker compose down        # conserva los datos de Prometheus y Grafana
docker compose down -v     # elimina también los volúmenes