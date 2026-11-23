import os
import time
import random
from flask import Flask, jsonify
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

INSTANCE_ID = os.getenv("INSTANCE_ID", "backend-desconocido")

# Métricas de Prometheus.
# Nota: la etiqueta se llama "instance_id" porque "instance" está reservada
# por Prometheus (identifica el target) y se renombraría a "exported_instance".
REQUEST_COUNT = Counter(
    "backend_http_requests_total",
    "Total de peticiones HTTP recibidas",
    ["method", "endpoint", "status", "instance_id"],
)

REQUEST_LATENCY = Histogram(
    "backend_http_request_duration_seconds",
    "Latencia de las peticiones HTTP en segundos",
    ["endpoint", "instance_id"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 1.0),
)


@app.route("/")
def index():
    start_time = time.time()
    status = "200"
    try:
        # Simula un procesamiento variable (entre 10 ms y 80 ms)
        time.sleep(random.uniform(0.01, 0.08))
        return jsonify({
            "mensaje": "Respuesta exitosa desde el cluster backend",
            "instancia": INSTANCE_ID,
        })
    except Exception:
        status = "500"
        raise
    finally:
        REQUEST_COUNT.labels(
            method="GET", endpoint="/", status=status, instance_id=INSTANCE_ID
        ).inc()
        REQUEST_LATENCY.labels(endpoint="/", instance_id=INSTANCE_ID).observe(
            time.time() - start_time
        )


@app.route("/health")
def health():
    # Usado por el healthcheck de Docker; no se contabiliza en las métricas.
    return jsonify({"estado": "ok", "instancia": INSTANCE_ID})


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
