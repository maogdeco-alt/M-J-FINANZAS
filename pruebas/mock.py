# Servidor de mentira que se hace pasar por Supabase, para poder probar la app sin tocar
# la base real (a la que, además, este entorno no tiene acceso).
import json, re, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DB = {"filas": {}, "reglas": {"params": {}, "bitacora": [], "firma": "", "actualizado": "2026-01-01T00:00:00Z", "actualizado_por": ""}}
LOCK = threading.Lock()
UID = "11111111-2222-3333-4444-555555555555"

def uid_de(correo):
    """Un identificador distinto por correo, como hace Supabase de verdad. Antes todos los
    correos compartían la MISMA fila, y eso hacía que una prueba de dos cuentas no probara nada."""
    import hashlib
    h = hashlib.md5((correo or "anon").strip().lower().encode()).hexdigest()
    return "%s-%s-%s-%s-%s" % (h[0:8], h[8:12], h[12:16], h[16:20], h[20:32])

def uid_de_ruta(path):
    """Saca el usuario_id de un ?usuario_id=eq.<uuid>."""
    import re as _re
    m = _re.search(r"usuario_id=eq\.([^&]+)", path or "")
    return m.group(1) if m else UID

def actualizado_de_ruta(path):
    """Saca la marca de un ?actualizado=eq.<marca>, o None si la petición no la pide."""
    import re as _re, urllib.parse as _u
    m = _re.search(r"[?&]actualizado=eq\.([^&]+)", path or "")
    return _u.unquote(m.group(1)) if m else None

def _instante(v):
    from datetime import datetime
    try: return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except Exception: return None

def misma_marca(a, b):
    """Postgres compara timestamptz como instantes, no como texto: '...Z' y '...+00:00' son iguales."""
    ia, ib = _instante(a), _instante(b)
    return ia is not None and ia == ib

def como_postgres(v):
    """Supabase devuelve la marca con '+00:00', no con la 'Z' que manda la app."""
    i = _instante(v)
    return i.isoformat(timespec="milliseconds") if i else v

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
            correo = b.get("email","a@gmail.com")
            return self._send(200, {"access_token":"tok","refresh_token":"ref","expires_in":3600,
                "user":{"id":uid_de(correo),"email":correo,
                        "user_metadata":{"name": b.get("data",{}).get("name","Prueba")}}})
        if "/auth/v1/logout" in p: return self._send(204, {})
        if "/rest/v1/radicados_datos" in p:
            u = uid_de_ruta(p)
            with LOCK: DB["filas"][u] = b if isinstance(b, dict) else (b[0] if b else {})
            return self._send(201, [DB["filas"][u]])
        return self._send(200, {})
    def do_PUT(self): return self._send(200, {"id":UID})
    def do_PATCH(self):
        p, b = self.path, self._body()
        if "/rest/v1/reglas_masivas" in p:
            with LOCK: DB["reglas"].update({k:v for k,v in b.items()})
            return self._send(200, [DB["reglas"]])
        if "/rest/v1/radicados_datos" in p:
            u = uid_de_ruta(p)
            with LOCK:
                fila = DB["filas"].setdefault(u, {})
                # Como PostgREST de verdad: un filtro ?actualizado=eq.<marca> que no coincide con
                # la fila NO cambia nada y responde una lista vacía. Antes este servidor de mentira
                # ignoraba el filtro, y por eso ninguna prueba vio nunca lo que pasa con dos
                # ventanas abiertas contra la Supabase real (ver t27_nube_dos_ventanas.py).
                esperado = actualizado_de_ruta(p)
                if esperado is not None and not misma_marca(fila.get("actualizado"), esperado):
                    return self._send(200, [])
                fila.update(b)
                if "actualizado" in b:
                    fila["actualizado"] = como_postgres(b["actualizado"])
            return self._send(200, [DB["filas"][u]])
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
            fila = DB["filas"].get(uid_de_ruta(p))
            return self._send(200, [fila] if fila else [])
        return self._send(200, [])

if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 9870), H).serve_forever()
