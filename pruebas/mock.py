# Servidor de mentira que se hace pasar por Supabase, para poder probar la app sin tocar
# la base real (a la que, además, este entorno no tiene acceso).
import json, re, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DB = {"filas": {}, "reglas": {"params": {}, "bitacora": [], "firma": "", "actualizado": "2026-01-01T00:00:00Z", "actualizado_por": ""}}
LOCK = threading.Lock()
UID = "11111111-2222-3333-4444-555555555555"

class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PATCH,PUT,DELETE,OPTIONS")
        self.send_header("Access-Control-Expose-Headers", "*")
    def _send(self, code, obj):
        cuerpo = json.dumps(obj).encode()
        self.send_response(code); self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers(); self.wfile.write(cuerpo)
    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if not n: return {}
        try: return json.loads(self.rfile.read(n).decode())
        except Exception: return {}
    def do_OPTIONS(self):
        self.send_response(204); self._cors()
        self.send_header("Content-Length","0"); self.end_headers()
    def do_POST(self):
        p, b = self.path, self._body()
        if "/auth/v1/token" in p or "/auth/v1/signup" in p:
            return self._send(200, {"access_token":"tok","refresh_token":"ref","expires_in":3600,
                "user":{"id":UID,"email":b.get("email","a@gmail.com"),
                        "user_metadata":{"name": b.get("data",{}).get("name","Prueba")}}})
        if "/auth/v1/logout" in p: return self._send(204, {})
        if "/rest/v1/radicados_datos" in p:
            with LOCK: DB["filas"][UID] = b if isinstance(b, dict) else (b[0] if b else {})
            return self._send(201, [DB["filas"][UID]])
        return self._send(200, {})
    def do_PUT(self): return self._send(200, {"id":UID})
    def do_PATCH(self):
        p, b = self.path, self._body()
        if "/rest/v1/reglas_masivas" in p:
            with LOCK: DB["reglas"].update({k:v for k,v in b.items()})
            return self._send(200, [DB["reglas"]])
        if "/rest/v1/radicados_datos" in p:
            with LOCK:
                fila = DB["filas"].setdefault(UID, {})
                fila.update(b)
            return self._send(200, [DB["filas"][UID]])
        return self._send(200, [])
    def do_DELETE(self):
        # /__reset deja la base de mentira en blanco: cada prueba arranca de cero.
        if self.path.startswith("/__reset"):
            with LOCK:
                DB["filas"].clear()
                DB["reglas"] = {"params": {}, "bitacora": [], "firma": "", "actualizado": "2026-01-01T00:00:00Z", "actualizado_por": ""}
            return self._send(200, {"ok": True})
        return self._send(200, {})
    def do_GET(self):
        p = self.path
        if "/rest/v1/profiles" in p: return self._send(200, [{"nombre":"Prueba","correo":"a@gmail.com"}])
        if "/rest/v1/reglas_masivas" in p: return self._send(200, [DB["reglas"]])
        if "/rest/v1/radicados_datos" in p:
            fila = DB["filas"].get(UID)
            return self._send(200, [fila] if fila else [])
        return self._send(200, [])

if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 9870), H).serve_forever()
