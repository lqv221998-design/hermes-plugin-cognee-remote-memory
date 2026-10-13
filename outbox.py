"""Durable immutable payload queue; Windows DPAPI, POSIX owner permissions."""
import ctypes,hashlib,json,os,sqlite3,time
from contextlib import contextmanager,closing
from pathlib import Path

def canonical(value):return json.dumps(value,ensure_ascii=False,separators=(',',':'))
def protect(data,decode=False):
    if os.name!='nt':return data
    class Blob(ctypes.Structure):_fields_=[('size',ctypes.c_ulong),('data',ctypes.POINTER(ctypes.c_ubyte))]
    buffer=ctypes.create_string_buffer(data);source=Blob(len(data),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte)));out=Blob()
    fn=ctypes.windll.crypt32.CryptUnprotectData if decode else ctypes.windll.crypt32.CryptProtectData
    if not fn(ctypes.byref(source),None,None,None,None,1,ctypes.byref(out)):raise OSError('DPAPI failed; payload not written/sent.')
    try:return ctypes.string_at(out.data,out.size)
    finally:
        free=ctypes.windll.kernel32.LocalFree;free.argtypes=[ctypes.c_void_p];free.restype=ctypes.c_void_p;free(ctypes.cast(out.data,ctypes.c_void_p))

class Outbox:
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, binding TEXT NOT NULL, payload BLOB NOT NULL, state TEXT NOT NULL, created REAL NOT NULL, receipt TEXT NOT NULL)')
        os.chmod(self.path,0o600)
    @contextmanager
    def db(self):
        with closing(sqlite3.connect(self.path,timeout=30)) as db:
            db.row_factory=sqlite3.Row
            try:yield db;db.commit()
            except BaseException:db.rollback();raise
    def enqueue(self,binding,payload):
        source=canonical(payload);group=hashlib.sha256((canonical(binding)+'\n'+source).encode()).hexdigest()
        parts=[source[i:i+60000] for i in range(0,len(source),60000)] or ['']
        with self.db() as db:
            for i,part in enumerate(parts,1):
                packet=canonical({'schema':'hermes-cognee-conversation-part-v1','record_id':group,'part_index':i,'part_total':len(parts),'authority':'unreviewed_conversation_not_normative','source_text':part})
                db.execute('INSERT OR IGNORE INTO events VALUES (?,?,?,?,?,?)',(group+':'+str(i),canonical(binding),protect(packet.encode()),'queued',time.time(),'{}'))
        return group
    def next_queued(self):
        with self.db() as db:row=db.execute("SELECT * FROM events WHERE state='queued' ORDER BY created,id LIMIT 1").fetchone()
        return self.decode(row) if row else None
    @staticmethod
    def decode(row):
        value=dict(row);value['binding']=json.loads(value['binding']);value['payload']=protect(value['payload'],decode=True).decode();value['receipt']=json.loads(value['receipt']);return value
    def status(self):
        value={s:0 for s in ['queued','sending','uncertain','raw_verified','indexed']}
        with self.db() as db:
            for state,count in db.execute('SELECT state,count(*) FROM events GROUP BY state'):value[state]=count
        return {**value,'payload_storage':'Windows DPAPI (current user)' if os.name=='nt' else 'POSIX 0600 plaintext; not encrypted'}
    def mark(self,row_id,state,receipt=None):
        with self.db() as db:db.execute('UPDATE events SET state=?,receipt=? WHERE id=?',(state,canonical(receipt or {}),row_id))
    def blocked(self):
        with self.db() as db:return db.execute("SELECT 1 FROM events WHERE state IN ('sending','uncertain','raw_verified') LIMIT 1").fetchone() is not None
    def flush(self,runtime,limit=4):
        if self.blocked():return self.status()
        for _ in range(limit):
            row=self.next_queued()
            if not row:break
            current=runtime.settings()
            if not current['capture'] or any(current[k]!=row['binding'].get(k) for k in ['endpoint','expected_user_id','expected_tenant_id','write_brain','device_id']):break
            try:
                client,brains=runtime.client();target=next((b for b in brains if b['id']==current['write_brain']),None)
                if not target or target['protected'] or not {'read','write'}<=set(target['permissions']):break
            except Exception:break
            with self.db() as db:
                db.execute('BEGIN IMMEDIATE')
                if db.execute("SELECT 1 FROM events WHERE state IN ('sending','uncertain','raw_verified') LIMIT 1").fetchone():break
                claimed=db.execute("UPDATE events SET state='sending' WHERE id=? AND state='queued'",(row['id'],)).rowcount
            if not claimed:continue
            try:
                result=client.send_packet(current['write_brain'],row['payload'],row['id'])
                verified=client.find_packet(current['write_brain'],row['id'],row['payload'])
                if not verified:raise ValueError('Raw not correlated.')
                terminal=isinstance(result,dict) and result.get('status')=='completed' and result.get('dataset_id')==current['write_brain'] and not result.get('error')
                self.mark(row['id'],'indexed' if terminal else 'raw_verified',{**verified,'terminal_response_verified':terminal})
                if not terminal:break
            except Exception:
                self.mark(row['id'],'uncertain',{'message':'Outcome uncertain. Read-only reconcile required; never resend blindly.'});break
        return self.status()
    def reconcile(self,runtime):
        client,_=runtime.client();current=runtime.settings()
        with self.db() as db:rows=[self.decode(x) for x in db.execute("SELECT * FROM events WHERE state IN ('sending','uncertain','raw_verified')")]
        for row in rows:
            if any(current[k]!=row['binding'].get(k) for k in ['endpoint','expected_user_id','expected_tenant_id','write_brain','device_id']):continue
            verified=client.find_packet(current['write_brain'],row['id'],row['payload'])
            if verified:self.mark(row['id'],'raw_verified',{**verified,'terminal_response_verified':False,'no_resend':True})
        return self.status()
