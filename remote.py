"""Remote-only policy transport derived from Cognee's pinned HttpBackend."""
import json
import re
import ssl
import copy
import hashlib
import uuid
import time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler, HTTPSHandler
from urllib.error import HTTPError, URLError
from .cognee_integration_hermes.http_backend import HttpBackend, _multipart_body
from .outbox import Outbox
UUID=re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
def literal_uuid(value):
    if not isinstance(value,str) or not UUID.fullmatch(value):raise ValueError('Invalid literal UUID.')
    return value

def origin_literal(value):
    if not isinstance(value,str) or value!=value.strip() or any(c in value for c in '\r\n\x00'):raise ValueError('URL must be an exact origin.')
    p=urlsplit(value)
    if p.scheme not in {'http','https'} or not p.hostname or p.username or p.password or p.path not in {'','/'} or p.query or p.fragment:raise ValueError('Enter origin only, without credentials or API path.')
    if p.scheme=='http' and p.hostname not in {'localhost','127.0.0.1','::1'}:raise ValueError('Remote URL requires trusted HTTPS.')
    _=p.port
    return value.rstrip('/')

class RemoteError(ValueError):
    def __init__(self,code='connection',status=0):
        self.code=code;self.status=status
        super().__init__('Cognee '+code+(f' (HTTP {status})' if status else ''))

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

class RemoteBackend(HttpBackend):
    def __init__(self,origin,read_key,*,opener=None):
        super().__init__(opener=opener)
        self._deadline:float|None=None
        self.url=origin_literal(origin);self.read_key=read_key
        self._safe_open=opener or build_opener(ProxyHandler({}),NoRedirect(),HTTPSHandler(context=ssl.create_default_context())).open
    def _request(self,method,path,*,timeout=20.0,json_body=None,multipart=None,parse_json=True,**kwargs):
        if self._deadline is not None:
            remaining=self._deadline-time.monotonic()
            if remaining<=0:raise RemoteError('read_budget_exhausted')
            timeout=min(timeout,remaining)
        uid=UUID.pattern
        allowed=(method=='POST' and path in {'/api/v1/recall','/api/v1/remember'}) or (method=='GET' and (path in {'/openapi.json','/api/v1/users/me','/api/v1/datasets'} or re.fullmatch(r'/api/v1/permissions/principals/'+uid+r'/datasets\?permission_name=(read|write)',path) or re.fullmatch(r'/api/v1/permissions/tenants/'+uid+r'/roles(?:/'+uid+r'/users)?',path) or re.fullmatch(r'/api/v1/datasets/'+uid+r'/data(?:/count|\?offset=\d+&limit=\d+|/'+uid+r'/raw)?',path)))
        if not allowed or kwargs:raise ValueError('Route/transport override prohibited.')
        headers={'Accept':'application/json','User-Agent':'hermes-cognee-remote-memory/0.1.1'}
        if path!='/openapi.json':
            key=self.read_key()
            if not isinstance(key,str) or len(key)<8 or len(key)>4096 or key!=key.strip() or any(c in key for c in '\r\n\x00*'):raise ValueError('Missing/invalid issued API key.')
            headers['X-Api-Key']=key
        data=None
        if json_body is not None:headers['Content-Type']='application/json';data=json.dumps(json_body,ensure_ascii=False).encode('utf-8')
        if multipart is not None:headers['Content-Type'],data=multipart
        try:
            with self._safe_open(Request(self.url+path,data=data,headers=headers,method=method),timeout=timeout) as response:
                raw=response.read(16000001)
                if len(raw)>16000000:raise RemoteError('response_limit')
                if parse_json and 'json' not in response.headers.get('Content-Type','').lower():raise RemoteError('not_json')
            return json.loads(raw) if parse_json else raw.decode('utf-8')
        except HTTPError as e:
            status=e.code;e.close()
            raise RemoteError({401:'credential_rejected',403:'permission_denied',404:'not_found',402:'provider_budget',429:'rate_limited'}.get(status,'http_error'),status) from None
        except (URLError,TimeoutError,OSError,UnicodeError):raise RemoteError('network_or_tls') from None
        except json.JSONDecodeError:raise RemoteError('invalid_json') from None
    def probe(self):
        who=self._request('GET','/api/v1/users/me',timeout=15)
        if not isinstance(who,dict) or who.get('is_active') is not True or who.get('is_superuser') is not False:raise RemoteError('ordinary_active_identity_required')
        literal_uuid(who.get('id'))
        if who.get('tenant_id'):literal_uuid(who['tenant_id'])
        spec=self._request('GET','/openapi.json',timeout=15);schemas=spec.get('components',{}).get('schemas',{})
        recall=schemas.get('RecallPayloadDTO',{}).get('properties',{})
        remember=schemas.get('Body_remember_api_v1_remember_post',{}).get('properties',{})
        if not {'datasetIds','onlyContext','includeReferences','scope','stream','searchType'}<=recall.keys() or not {'raw_data','datasetId','external_metadata','self_improvement','run_in_background'}<=remember.keys():raise RemoteError('incompatible_api_contract')
        return {'identity':{'id':who['id'],'tenant_id':who.get('tenant_id') or ''},'brains':self.directory(who)}
    def directory(self,who):
        principals=[literal_uuid(who['id'])];tenant=who.get('tenant_id')
        if tenant:
            principals.append(literal_uuid(tenant))
            for role in self._rows(self._request('GET',f'/api/v1/permissions/tenants/{tenant}/roles',timeout=15)):
                rid=literal_uuid(role['id']);members=self._rows(self._request('GET',f'/api/v1/permissions/tenants/{tenant}/roles/{rid}/users',timeout=15))
                if any(m.get('id')==who['id'] for m in members):principals.append(rid)
        found={}
        for principal in dict.fromkeys(principals):
            for perm in ['read','write']:
                rows=self._rows(self._request('GET',f'/api/v1/permissions/principals/{principal}/datasets?permission_name={perm}',timeout=15))
                for row in rows:
                    bid=literal_uuid(row['id']);item=found.setdefault(bid,{'id':bid,'name':str(row.get('name') or bid),'permissions':[]})
                    if perm not in item['permissions']:item['permissions'].append(perm)
        for row in self._rows(self._request('GET','/api/v1/datasets',timeout=15)):
            bid=literal_uuid(row['id']);item=found.setdefault(bid,{'id':bid,'name':str(row.get('name') or bid),'permissions':[]})
            if 'read' not in item['permissions']:item['permissions'].append('read')
        for item in found.values():
            item['permissions']=sorted(item['permissions']);item['protected']=item['name'] in {'qaqc_company_standard','qaqc_legal_standard'}
        return sorted(found.values(),key=lambda x:(x['name'],x['id']))
    @staticmethod
    def _rows(rows):
        if not isinstance(rows,list) or len(rows)>10000 or any(not isinstance(r,dict) or not UUID.fullmatch(r.get('id','')) for r in rows):raise RemoteError('invalid_directory')
        if len({r['id'] for r in rows})!=len(rows):raise RemoteError('duplicate_directory')
        return rows
    def recall(self,*,query,datasets,top_k=5,timeout:float=20.0,**kwargs):
        if not isinstance(datasets,list) or not datasets or len(datasets)>20 or len(set(datasets))!=len(datasets):raise ValueError('Explicit Brain UUIDs required.')
        for value in datasets:literal_uuid(value)
        if not isinstance(query,str) or not query.strip() or len(query)>4000 or type(top_k) is not int or not 1<=top_k<=20:raise ValueError('Invalid recall query/budget.')

        payload={'query':query,'datasetIds':datasets,'searchType':'HYBRID_COMPLETION','topK':top_k,'onlyContext':True,'includeReferences':True,'scope':'graph','stream':False,'verbose':False}
        value=self._request('POST','/api/v1/recall',timeout=timeout,json_body=payload)
        results=value if isinstance(value,list) else value.get('results') if isinstance(value,dict) else None
        if not isinstance(results,list):raise ValueError('Invalid recall response.')
        if any(not isinstance(item,dict) or item.get('dataset_id') not in [None,*datasets] for item in results):raise ValueError('Out-of-scope recall response.')
        return results
    def send_packet(self,dataset,payload,record_id):
        literal_uuid(dataset)
        if not isinstance(payload,str) or len(payload)>200000 or not isinstance(json.loads(payload),dict):raise ValueError('Invalid JSON archive packet.')
        fields={'datasetId':dataset,'raw_data':payload,'self_improvement':'false','run_in_background':'false','external_metadata':json.dumps([{'hermes_cognee_record_id':record_id,'sha256':hashlib.sha256(payload.encode()).hexdigest(),'review_status':'unreviewed','source':'hermes_remote_conversation'}])}
        return self._request('POST','/api/v1/remember',timeout=300,multipart=_multipart_body(fields,{}))
    def find_packet(self,dataset,record_id,expected):
        literal_uuid(dataset);base=f'/api/v1/datasets/{dataset}/data'
        count=self._request('GET',base+'/count',timeout=20).get('count')
        if type(count) is not int or not 0<=count<=10000:raise RemoteError('inventory_limit')
        rows=[]
        while len(rows)<count:
            page=self._rows(self._request('GET',base+f'?offset={len(rows)}&limit={min(100,count-len(rows))}',timeout=20))
            if not page:raise RemoteError('inventory_incomplete')
            rows.extend(page)
            if len(rows)>count:raise RemoteError('inventory_changed')
        if self._request('GET',base+'/count',timeout=20).get('count')!=count or len({r['id'] for r in rows})!=len(rows) or any(r.get('datasetId')!=dataset for r in rows):raise RemoteError('inventory_changed')
        matches=[r for r in rows if (r.get('externalMetadata') or {}).get('hermes_cognee_record_id')==record_id]
        if not matches:return None
        if len(matches)!=1:raise RemoteError('duplicate_record')
        data_id=literal_uuid(matches[0]['id']);raw=self._request('GET',base+'/'+data_id+'/raw',timeout=20,parse_json=False)
        if raw!=expected:raise RemoteError('raw_mismatch')
        return {'data_id':data_id,'sha256':hashlib.sha256(raw.encode()).hexdigest()}

ID='cognee-remote-memory'
KEY_SLOT='COGNEE_REMOTE_MEMORY_API_KEY'
DEFAULTS={'endpoint':'','expected_user_id':'','expected_tenant_id':'','write_brain':'','read_brains':[],'capture':False,'auto_recall':False,'device_id':''}

class Runtime:
    def __init__(self,home,read_config,write_config,read_secret,write_secret,*,backend_factory=RemoteBackend,current_home=None):
        self.home=Path(home).resolve();self.read_config=read_config;self.write_config=write_config
        self.read_secret=read_secret;self.write_secret=write_secret;self.backend_factory=backend_factory
        self.current_home=current_home or (lambda:self.home)
    def scope(self):
        if Path(self.current_home()).resolve()!=self.home:raise RemoteError('profile_changed')
    def settings(self):
        self.scope();cfg=self.read_config() or {};entry=cfg.get('plugins',{}).get('entries',{}).get(ID,{})
        return {**copy.deepcopy(DEFAULTS),**{k:v for k,v in {**entry.get('config',{}),**entry.get('settings',{})}.items() if k in DEFAULTS}}
    def save(self,value):
        self.scope();cfg=copy.deepcopy(self.read_config() or {})
        cfg.setdefault('plugins',{}).setdefault('entries',{}).setdefault(ID,{})['settings']=copy.deepcopy(value)
        self.write_config(cfg)
        if self.settings()!=value:raise RemoteError('settings_not_saved')
    def public(self):
        s=self.settings();cfg=self.read_config() or {}
        return {**s,'has_api_key':bool(self.read_secret()),'configured':bool(s['endpoint'] and s['expected_user_id']),'provider':cfg.get('memory',{}).get('provider',''),'strategy':'HYBRID_COMPLETION','only_context':True,'secret_storage':'profile .env + OS permissions; not encrypted vault'}
    def connect(self,body):
        if not isinstance(body,dict) or set(body)!={'endpoint','api_key'}:raise ValueError('Unexpected connection fields.')
        old=self.settings();origin=origin_literal(body['endpoint']);key=body['api_key']
        if not isinstance(key,str):raise ValueError('Invalid key.')
        if not key:
            if old['endpoint']!=origin:raise ValueError('New origin requires its own issued key.')
            key=self.read_secret()
        if not key or key!=key.strip() or any(x in key for x in '\r\n\x00*') or len(key)>4096:raise ValueError('Invalid issued key.')
        result=self.backend_factory(origin,lambda:key).probe();identity=result['identity']
        value=copy.deepcopy(DEFAULTS);value['device_id']=old['device_id'] or uuid.uuid4().hex
        self.save(value)
        self.write_secret(key)
        if self.read_secret()!=key:raise RemoteError('credential_not_saved')
        value.update(endpoint=origin,expected_user_id=literal_uuid(identity['id']),expected_tenant_id=identity['tenant_id'])
        self.save(value)
        return {**result,'saved':True,'corpus_writes':False,'activation_changed':False}
    def client(self,deadline=None):
        s=self.settings();origin=origin_literal(s['endpoint']);literal_uuid(s['expected_user_id'])
        def key():
            self.scope();now=self.settings()
            if any(now[k]!=s[k] for k in ['endpoint','expected_user_id','expected_tenant_id']):raise RemoteError('connection_changed')
            return self.read_secret()
        client=self.backend_factory(origin,key)
        if deadline is not None:client._deadline=deadline
        result=client.probe()
        if result['identity']!={'id':s['expected_user_id'],'tenant_id':s['expected_tenant_id']}:raise RemoteError('identity_or_tenant_changed')
        return client,result['brains']
    def save_selection(self,body):
        fields={'write_brain','read_brains','capture','auto_recall','acknowledge_sharing'}
        if not isinstance(body,dict) or set(body)!=fields or any(type(body[k]) is not bool for k in ['capture','auto_recall','acknowledge_sharing']):raise ValueError('Invalid memory selection.')
        write=body['write_brain'];read=body['read_brains']
        if write:literal_uuid(write)
        if not isinstance(read,list) or len(read)>20 or len(set(read))!=len(read):raise ValueError('Invalid read Brain list.')
        for bid in read:literal_uuid(bid)
        _,brains=self.client();by={b['id']:b for b in brains}
        if write and (write not in by or by[write]['protected'] or not {'read','write'}<=set(by[write]['permissions'])):raise RemoteError('conversation_brain_requires_read_write_non_normative')
        if any(bid not in by or 'read' not in by[bid]['permissions'] for bid in read):raise RemoteError('selected_read_acl_denied')
        if body['capture'] and (not write or not body['acknowledge_sharing']):raise ValueError('Select and acknowledge conversation sharing/egress.')
        if body['auto_recall'] and not read:raise ValueError('Select recall Brains.')
        value=self.settings();value.update({k:body[k] for k in fields if k!='acknowledge_sharing'});self.save(value)
        return {'saved':True,**self.public()}
    def activate(self,body):
        if body!={'acknowledge_replace':True}:raise ValueError('Explicit provider replacement acknowledgement required.')
        s=self.settings();self.client()
        if not s['read_brains'] and not (s['capture'] and s['write_brain']):raise ValueError('Configure memory destinations first.')
        cfg=copy.deepcopy(self.read_config() or {});enabled=cfg.get('plugins',{}).get('enabled',[])
        if ID not in enabled:raise RemoteError('plugin_not_enabled')
        if any(p in enabled for p in ['cognee-admin','qaqc-cognee','cognee']):raise RemoteError('existing_cognee_writer_enabled')
        cfg.setdefault('memory',{})['provider']=ID;self.write_config(cfg)
        if (self.read_config() or {}).get('memory',{}).get('provider')!=ID:raise RemoteError('activation_not_saved')
        return {'saved':True,'provider':ID,'new_session_required':True,'live_activation_verified':False}
    def disconnect(self):
        s=self.settings();value=copy.deepcopy(DEFAULTS);value['device_id']=s['device_id'];self.save(value)
        self.write_secret('')
        return {'disconnected':True,'key_revoked_on_server':False,'outbox_preserved':True,'new_session_required':True}
