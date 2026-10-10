import http.server, functools, os, sys
d = sys.argv[1]; port = int(sys.argv[2])
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=d)
class Q(H.func):
    def log_message(self,*a): pass
http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=d)).serve_forever()
