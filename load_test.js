import http from 'k6/http';
import { check, sleep } from 'k6';

// Perfil de carga (60 s): rampa a 50 usuarios, meseta de 50 usuarios, descenso a 0.
export const options = {
  stages: [
    { duration: '15s', target: 50 }, // rampa de ascenso hasta 50 usuarios virtuales
    { duration: '30s', target: 50 }, // meseta: 50 usuarios simultáneos
    { duration: '15s', target: 0 },  // rampa de descenso
  ],
  thresholds: {
    http_req_failed: ['rate<0.01'],    // menos de 1 % de errores
    http_req_duration: ['p(95)<200'],  // p95 de latencia menor a 200 ms
    checks: ['rate>0.99'],
  },
};

// Por defecto apunta a Nginx en el host. Con k6 en Docker: -e BASE_URL=http://host.docker.internal
const BASE_URL = __ENV.BASE_URL || 'http://localhost';

export default function () {
  const res = http.get(`${BASE_URL}/`);
  check(res, {
    'estado es 200': (r) => r.status === 200,
    'responde con instancia': (r) => r.json('instancia') !== undefined,
  });
  sleep(0.1);}
