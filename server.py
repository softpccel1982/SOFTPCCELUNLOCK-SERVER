import json, os, secrets, hashlib, hmac, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

HOST = os.getenv('HOST','0.0.0.0')
PORT = int(os.getenv('PORT','8765'))
USER = os.getenv('ADMIN_USER','admin')
PASSWORD = os.getenv('ADMIN_PASSWORD','')
if not PASSWORD:
    raise SystemExit('Configure ADMIN_PASSWORD antes de iniciar o servidor.')
TOKENS = {}
MODELS = ['Xiaomi','Redmi','POCO']
class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, data):
        raw=json.dumps(data,ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(raw)))
        self.send_header('Cache-Control','no-store')
        self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/health': return self.send_json(200,{'status':'online','product':'SOFTPCCELUNLOCK','version':'0.1'})
        if path=='/api/models':
            token=self.headers.get('Authorization','').removeprefix('Bearer ').strip()
            if token not in TOKENS or TOKENS[token]<time.time(): return self.send_json(401,{'error':'Não autorizado'})
            return self.send_json(200,{'brands':MODELS,'frp_removal':'not_implemented','modes':['ADB','Fastboot','Mi Assistant (diagnóstico)']})
        self.send_json(404,{'error':'Rota não encontrada'})
    def do_POST(self):
        if urlparse(self.path).path!='/api/login': return self.send_json(404,{'error':'Rota não encontrada'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<1 or size>4096: return self.send_json(400,{'error':'Tamanho inválido'})
            data=json.loads(self.rfile.read(size))
            ok=hmac.compare_digest(str(data.get('username','')),USER) and hmac.compare_digest(str(data.get('password','')),PASSWORD)
            if not ok: return self.send_json(401,{'error':'Credenciais inválidas'})
            token=secrets.token_urlsafe(32); TOKENS[token]=time.time()+3600
            return self.send_json(200,{'token':token,'expires_in':3600})
        except (ValueError,TypeError,json.JSONDecodeError): self.send_json(400,{'error':'JSON inválido'})
if __name__=='__main__':
    print(f'SOFTPCCELUNLOCK API escutando em {HOST}:{PORT}; configure HTTPS no provedor')
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
