"""Local demonstration server; bind to loopback, not a production deployment."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .report import ROOT, run


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, data, content_type='application/json; charset=utf-8'):
        body=data if isinstance(data,bytes) else json.dumps(data,allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Cache-Control','no-store')
        self.end_headers();self.wfile.write(body)

    def do_GET(self):
        if self.path=='/':
            self.respond(200,(ROOT/'web/index.html').read_bytes(),'text/html; charset=utf-8')
        elif self.path=='/api/report':
            try:self.respond(200,run())
            except ValueError as exc:self.respond(400,{'error':str(exc)})
        elif self.path=='/health':self.respond(200,{'status':'ok'})
        else:self.respond(404,{'error':'Route not found.'})

    def do_POST(self):
        if self.path!='/api/plan':return self.respond(404,{'error':'Route not found.'})
        # JSON only. Cross-origin forms cannot trigger changes or expensive planning calls.
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':
            return self.respond(415,{'error':'Use application/json.'})
        origin=self.headers.get('Origin')
        if origin and origin not in {f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'}:
            return self.respond(403,{'error':'Cross-origin requests are disabled.'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 1<=length<=8192:raise ValueError('JSON body must be 1–8192 bytes.')
            data=json.loads(self.rfile.read(length))
            if not isinstance(data,dict):raise ValueError('Expected a JSON object.')
            self.respond(200,run(budget=data.get('budget'),movement=float(data.get('movement',.30))))
        except (ValueError,TypeError,OverflowError) as exc:self.respond(400,{'error':str(exc)})


def serve(port=8010):
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    print(f'MarketMix demo: http://127.0.0.1:{server.server_port}')
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
