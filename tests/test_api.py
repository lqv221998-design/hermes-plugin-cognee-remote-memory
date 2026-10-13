import importlib,pathlib
from fastapi import FastAPI
import asyncio,httpx
from test_runtime import make,ID
from test_remote import BRAIN

class TestClient:
    __test__=False
    def __init__(self,app):self.app=app
    def request(self,method,url,**kwargs):
        async def run():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app),base_url='http://fixture') as client:return await client.request(method,url,**kwargs)
        return asyncio.run(run())
    def get(self,url,**kwargs):return self.request('GET',url,**kwargs)
    def post(self,url,**kwargs):return self.request('POST',url,**kwargs)

def api(tmp_path):
    import forkplugin
    assert pathlib.Path(forkplugin.__path__[0],'dashboard/plugin_api.py').exists(),'Desktop connection API missing'
    module=importlib.import_module('forkplugin.dashboard.plugin_api');r,c=make(tmp_path)
    app=FastAPI();app.include_router(module.create_router(lambda:r),prefix='/api/plugins/'+ID)
    return TestClient(app),r,c

def test_form_connection_selection_and_explicit_activation(tmp_path):
    a,r,c=api(tmp_path);prefix='/api/plugins/'+ID
    result=a.post(prefix+'/connect',json={'endpoint':'https://cognee.example','api_key':'fixture-key'})
    assert result.status_code==200 and 'fixture-key' not in result.text
    assert a.get(prefix+'/connections').json()['provider']=='hindsight'
    selection={'write_brain':BRAIN,'read_brains':[BRAIN],'capture':True,'auto_recall':True,'acknowledge_sharing':True}
    assert a.post(prefix+'/selection',json=selection).status_code==200
    assert a.post(prefix+'/activate',json={'acknowledge_replace':False}).status_code==400
    assert c.cfg['memory']['provider']=='hindsight'
    assert a.post(prefix+'/activate',json={'acknowledge_replace':True}).status_code==200
    assert c.cfg['memory']['provider']==ID

def test_invalid_request_never_echoes_secret(tmp_path):
    a,r,c=api(tmp_path);s='fixture-not-to-echo'
    response=a.post('/api/plugins/'+ID+'/connect',content='{secret:'+s)
    assert response.status_code==400 and s not in response.text
