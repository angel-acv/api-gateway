"""Microservicio generico (Ventas / Inventario) sin dependencias externas.

Uso:  python servicio.py <ventas|inventario> <puerto>
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

NOMBRE = sys.argv[1] if len(sys.argv) > 1 else "ventas"
PUERTO = int(sys.argv[2]) if len(sys.argv) > 2 else 5001

DATOS = {
    "ventas": [{"id": 1, "producto": "Laptop", "total": 3200000},
               {"id": 2, "producto": "Mouse", "total": 45000}],
    "inventario": [{"sku": "A-100", "producto": "Laptop", "stock": 12},
                   {"sku": "B-200", "producto": "Mouse", "stock": 80}],
}


class Handler(BaseHTTPRequestHandler):
    def _json(self, codigo, cuerpo):
        datos = json.dumps(cuerpo, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):
        ruta = self.path.split("?")[0]
        if ruta == "/health":
            return self._json(200, {"status": "Healthy", "servicio": NOMBRE, "puerto": PUERTO})
        # El gateway reenvia el path completo: /ventas/... o /inventario/...
        if ruta.startswith(f"/{NOMBRE}"):
            return self._json(200, {"servicio": NOMBRE, "puerto": PUERTO,
                                    "path": ruta, "datos": DATOS[NOMBRE]})
        self._json(404, {"error": "no encontrado", "path": ruta})

    def log_message(self, fmt, *args):
        print(f"[{NOMBRE}:{PUERTO}] {self.command} {self.path} -> {args[1] if len(args) > 1 else ''}", flush=True)


class Servidor(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        # El cliente (p. ej. el health check de YARP) cerro la conexion antes de leer la respuesta: es inofensivo.
        if isinstance(sys.exc_info()[1], ConnectionError):
            return
        super().handle_error(request, client_address)


if __name__ == "__main__":
    print(f"Servicio '{NOMBRE}' escuchando en http://localhost:{PUERTO}/ (Ctrl+C para detener)", flush=True)
    Servidor(("localhost", PUERTO), Handler).serve_forever()
