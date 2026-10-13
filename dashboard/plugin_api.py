"""Profile-scoped, credential-redacted Desktop API; outer Hermes auth required."""
import importlib.util,json,sys
from pathlib import Path
from threading import RLock
from fastapi import APIRouter,HTTPException,Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
try:
    from ..provider import native_runtime
    from ..remote import ID,RemoteError,Outbox
except ImportError:
    root=Path(__file__).resolve().parents[1];alias='_hermes_cognee_remote_ui'
    if alias not in sys.modules:
        spec=importlib.util.spec_from_file_location(alias,root/'__init__.py',submodule_search_locations=[str(root)])
        assert spec is not None and spec.loader is not None
        package=importlib.util.module_from_spec(spec);sys.modules[alias]=package;spec.loader.exec_module(package)
    native_runtime=__import__(alias+'.provider',fromlist=['native_runtime']).native_runtime
    m=__import__(alias+'.remote',fromlist=['ID']);ID=m.ID;RemoteError=m.RemoteError;Outbox=m.Outbox
LOCK=RLock();HEADERS={'Cache-Control':'no-store'}
def create_router(factory):
    api=APIRouter()
    def runtime():
        r=factory();cfg=r.read_config() or {};plugins=cfg.get('plugins',{})
        if ID not in plugins.get('enabled',[]) or ID in plugins.get('disabled',[]):raise HTTPException(404,'Plugin disabled.',headers=HEADERS)
        return r
    def box(r):return Outbox(r.home/'plugin-data'/ID/'outbox.sqlite3')
    @api.get('/connections')
    def connections():
        with LOCK:
            r=runtime();return JSONResponse({**r.public(),'outbox':box(r).status()},headers=HEADERS)
    @api.get('/brains')
    def brains():
        try:
            with LOCK:return JSONResponse({'brains':runtime().client()[1]},headers=HEADERS)
        except RemoteError as e:raise HTTPException(400,str(e),headers=HEADERS) from None
        except HTTPException:raise
        except Exception:raise HTTPException(400,'Brain directory unavailable; check URL, identity and ACL.',headers=HEADERS) from None
    async def action(request,operation):
        try:
            raw=await request.body()
            if len(raw)>32768:raise ValueError()
            body=json.loads(raw or b'{}')
        except Exception:raise HTTPException(400,'Invalid form.',headers=HEADERS) from None
        def work():
            with LOCK:
                r=runtime()
                try:
                    if operation=='connect':return r.connect(body)
                    if operation=='selection':return r.save_selection(body)
                    if operation=='activate':return r.activate(body)
                    if body!={}:raise ValueError()
                    if operation=='disconnect':return r.disconnect()
                    if operation=='flush':return box(r).flush(r)
                    if operation=='reconcile':return box(r).reconcile(r)
                    raise ValueError()
                except RemoteError as e:raise HTTPException(400,str(e),headers=HEADERS) from None
                except Exception:raise HTTPException(400,'Rejected. Check form, identity, ACL and consent; no credential details are returned.',headers=HEADERS) from None
        return JSONResponse(await run_in_threadpool(work),headers=HEADERS)
    @api.post('/connect')
    async def connect(request:Request):return await action(request,'connect')
    @api.post('/selection')
    async def selection(request:Request):return await action(request,'selection')
    @api.post('/activate')
    async def activate(request:Request):return await action(request,'activate')
    @api.post('/disconnect')
    async def disconnect(request:Request):return await action(request,'disconnect')
    @api.post('/flush')
    async def flush(request:Request):return await action(request,'flush')
    @api.post('/reconcile')
    async def reconcile(request:Request):return await action(request,'reconcile')
    return api
router=create_router(native_runtime)
