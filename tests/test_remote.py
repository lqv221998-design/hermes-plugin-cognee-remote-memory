import importlib,io,json,pathlib,sys,types
import pytest
ROOT=pathlib.Path(__file__).resolve().parents[1];PLUGIN=ROOT
sys.path.insert(0,str(PLUGIN))
pkg=types.ModuleType('forkplugin');pkg.__path__=[str(PLUGIN)];sys.modules.setdefault('forkplugin',pkg)
UID='11111111-1111-4111-8111-111111111111'
BRAIN='22222222-2222-4222-8222-222222222222'
OTHER='33333333-3333-4333-8333-333333333333'
class Response(io.BytesIO):
    def __init__(self,value):super().__init__(json.dumps(value).encode());self.headers={'Content-Type':'application/json'}
    def __enter__(self):return self
    def __exit__(self,*args):return False
class Wire:
    def __init__(self):self.requests=[]
    def __call__(self,request,timeout=None):
        self.requests.append(request)
        return Response([{'text':'bằng chứng','dataset_id':BRAIN,'references':[{'data_id':OTHER}]}])
    def last(self):return json.loads(self.requests[-1].data)
def backend(wire):
    if (PLUGIN/'remote.py').exists():return importlib.import_module('forkplugin.remote').RemoteBackend('https://cognee.example',lambda:'fixture-key',opener=wire)
    from cognee_integration_hermes.http_backend import HttpBackend
    result=HttpBackend(opener=wire);result.url='https://cognee.example';result.api_key='fixture-key';return result

def test_default_recall_is_scoped_hybrid_context_only():
    wire=Wire();client=backend(wire)
    client.recall(query='Quy định nghiệm thu?',datasets=[BRAIN],session_id='private-session',top_k=5,auto_route=True,query_type=None,timeout=5)
    body=wire.last()
    assert body.get('searchType')=='HYBRID_COMPLETION',body
    assert body.get('datasetIds')==[BRAIN]
    assert body.get('onlyContext') is True and body.get('includeReferences') is True
    assert body.get('scope')=='graph' and body.get('stream') is False
    assert 'session_id' not in body and 'datasets' not in body

@pytest.mark.parametrize('origin',['http://192.0.2.42:8443','https://u:p@cognee.example','https://cognee.example/api/v1','https://cognee.example?key=x',' https://cognee.example','https://cognee.example/#x'])
def test_refuses_unsafe_origin(origin):
    cls=importlib.import_module('forkplugin.remote').RemoteBackend
    with pytest.raises(ValueError):cls(origin,lambda:'fixture-key')

def test_no_provisioning_routes():
    c=backend(Wire())
    with pytest.raises(ValueError):c.ensure_dataset(dataset='new_brain',timeout=5)

def test_masked_key_never_sent():
    cls=importlib.import_module('forkplugin.remote').RemoteBackend
    w=Wire();c=cls('https://cognee.example',lambda:'********',opener=w)
    with pytest.raises(ValueError):c.recall(query='q',datasets=[BRAIN])
    assert w.requests==[]

def test_probe_does_not_write():
    cls=importlib.import_module('forkplugin.remote').RemoteBackend
    assert callable(getattr(cls,'probe',None)),'Authenticated connection probe missing'
    class ProbeWire(Wire):
        def __call__(self,request,timeout=None):
            self.requests.append(request)
            if request.selector=='/api/v1/users/me':return Response({'id':UID,'tenant_id':None,'is_superuser':False,'is_active':True})
            if request.selector=='/openapi.json':return Response({'components':{'schemas':{'RecallPayloadDTO':{'properties':dict.fromkeys(['datasetIds','onlyContext','includeReferences','scope','stream','searchType'])},'Body_remember_api_v1_remember_post':{'properties':dict.fromkeys(['raw_data','datasetId','external_metadata','self_improvement','run_in_background'])}}}})
            return Response([{'id':BRAIN,'name':'conversation'}])
    w=ProbeWire();p=cls('https://cognee.example',lambda:'fixture-key',opener=w).probe()
    assert p['identity']['id']==UID and p['brains'][0]['permissions']==['read','write']
    assert all(r.get_method()=='GET' for r in w.requests)

def test_errors_do_not_echo_backend_secrets():
    from urllib.error import HTTPError
    secret='fixture-sensitive-do-not-echo'
    def fail(request,timeout=None):raise HTTPError(request.full_url,401,'bad',{},io.BytesIO(secret.encode()))
    c=backend(fail)
    with pytest.raises(Exception) as e:c.recall(query='q',datasets=[BRAIN])
    assert secret not in str(e.value)

def test_archive_wire_and_raw_readback():
    cls=importlib.import_module('forkplugin.remote').RemoteBackend
    assert callable(getattr(cls,'send_packet',None)),'Permanent JSON archive transport missing'
    from email.parser import BytesParser
    from email.policy import default
    packet=json.dumps({'schema':'test-transcript','messages':[{'role':'user','content':'Tiếng Việt'}]},ensure_ascii=False)
    class ArchiveWire(Wire):
        def __call__(self,request,timeout=None):
            self.requests.append(request)
            if request.get_method()=='POST':
                mime=BytesParser(policy=default).parsebytes(('Content-Type: '+request.get_header('Content-type')+'\r\n\r\n').encode()+request.data)
                self.fields={p.get_param('name',header='content-disposition'):p.get_payload(decode=True).decode() for p in mime.iter_parts()}
                return Response({'status':'completed','dataset_id':BRAIN})
            if request.selector.endswith('/count'):return Response({'count':1})
            if request.selector.endswith('/raw'):
                result=Response({});result.seek(0);result.truncate();result.write(packet.encode());result.seek(0);return result
            return Response([{'id':OTHER,'datasetId':BRAIN,'externalMetadata':{'hermes_cognee_record_id':'record:1'}}])
    wire=ArchiveWire();client=cls('https://cognee.example',lambda:'fixture-key',opener=wire)
    client.send_packet(BRAIN,packet,'record:1')
    assert wire.fields['datasetId']==BRAIN and wire.fields['self_improvement']=='false' and wire.fields['run_in_background']=='false'
    assert wire.fields['raw_data']==packet and 'session_id' not in wire.fields
    assert client.find_packet(BRAIN,'record:1',packet)['data_id']==OTHER
