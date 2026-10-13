"""Real browser + real HTTP against an explicitly synthetic Cognee API fixture."""
import importlib,json,pathlib,socket,threading,time,uuid,hashlib
from email.parser import BytesParser
from email.policy import default
import pytest
from fastapi import FastAPI,Request,HTTPException
from fastapi.responses import HTMLResponse,Response
from playwright.sync_api import sync_playwright,expect
from test_remote import UID,BRAIN,OTHER,ROOT
from test_runtime import MemoryConfig,ID

@pytest.fixture
def fixture_server(tmp_path):
    import uvicorn
    m=importlib.import_module('forkplugin.remote');api=importlib.import_module('forkplugin.dashboard.plugin_api')
    c=MemoryConfig();r=m.Runtime(tmp_path,c.read,c.write,lambda:c.key,lambda k:setattr(c,'key',k))
    app=FastAPI(openapi_url=None);records=[];recalls=[]
    def auth(request):
        if request.headers.get('X-Api-Key')!='fixture-http-key':raise HTTPException(401,'Fixture key rejected')
    @app.get('/api/v1/users/me')
    def who(request:Request):auth(request);return {'id':UID,'tenant_id':None,'is_active':True,'is_superuser':False}
    @app.get('/openapi.json')
    def spec():return {'components':{'schemas':{'RecallPayloadDTO':{'properties':dict.fromkeys(['datasetIds','onlyContext','includeReferences','scope','stream','searchType'])},'Body_remember_api_v1_remember_post':{'properties':dict.fromkeys(['raw_data','datasetId','external_metadata','self_improvement','run_in_background'])}}}}
    @app.get('/api/v1/datasets')
    def datasets(request:Request):auth(request);return [{'id':BRAIN,'name':'conversation'},{'id':OTHER,'name':'qaqc_company_standard'}]
    @app.get('/api/v1/permissions/principals/{principal}/datasets')
    def permissions(principal:str,permission_name:str,request:Request):
        auth(request);return [{'id':BRAIN,'name':'conversation'}]+([{'id':OTHER,'name':'qaqc_company_standard'}] if permission_name=='read' else [])
    @app.post('/api/v1/recall')
    async def recall(request:Request):
        auth(request);p=await request.json();recalls.append(p)
        if not p.get('datasetIds') or any(x not in [BRAIN,OTHER] for x in p['datasetIds']):raise HTTPException(403,'Fixture scope denied')
        return [{'text':'PUBLIC FIXTURE: nghiệm thu theo nguồn đã kiểm.','dataset_id':p['datasetIds'][0],'references':[{'data_id':OTHER}]}]
    @app.post('/api/v1/remember')
    async def remember(request:Request):
        auth(request);body=await request.body();mime=BytesParser(policy=default).parsebytes(('Content-Type: '+request.headers['Content-Type']+'\r\n\r\n').encode()+body)
        fields={p.get_param('name',header='content-disposition'):p.get_payload(decode=True).decode() for p in mime.iter_parts()}
        if fields['datasetId']!=BRAIN:raise HTTPException(403,'Fixture write denied')
        raw=fields['raw_data'];data_id=str(uuid.uuid4());records.append({'id':data_id,'datasetId':BRAIN,'raw':raw,'externalMetadata':json.loads(fields['external_metadata'])[0]})
        return {'status':'completed','dataset_id':BRAIN,'items_processed':len(records),'items':[{'id':x['id']} for x in records]}
    @app.get('/api/v1/datasets/{dataset}/data/count')
    def count(dataset:str,request:Request):auth(request);return {'count':len(records)}
    @app.get('/api/v1/datasets/{dataset}/data')
    def data(dataset:str,request:Request,offset:int=0,limit:int=100):auth(request);return [{k:v for k,v in x.items() if k!='raw'} for x in records[offset:offset+limit]]
    @app.get('/api/v1/datasets/{dataset}/data/{data_id}/raw')
    def raw(dataset:str,data_id:str,request:Request):auth(request);return Response(next(x['raw'] for x in records if x['id']==data_id),media_type='text/plain')
    app.include_router(api.create_router(lambda:r),prefix='/api/plugins/'+ID)
    @app.get('/')
    def page():return HTMLResponse('<!doctype html><meta charset="utf-8"><title>Cognee Memory — SDK/HTTP fixture</title><style>:root{--ui-stroke-secondary:#ccc;--ui-text-secondary:#222}body{font:14px Arial;background:#fafafa}button,input,select{font:inherit;padding:7px}button{margin-right:8px}</style><div id="root"></div><script src="/bundle.js"></script>')
    @app.get('/bundle.js')
    def bundle():return Response((ROOT/'evidence/ui-fixture-bundle.js').read_bytes(),media_type='text/javascript')
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,log_level='error'));thread=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True);thread.start()
    # Readiness uses socket startup state, not a blind fixed delay.
    deadline=time.monotonic()+10
    while not server.started and thread.is_alive() and time.monotonic()<deadline:time.sleep(.01)
    assert server.started
    try:yield f'http://127.0.0.1:{port}',r,c,records,recalls
    finally:server.should_exit=True;thread.join(timeout=5);sock.close();assert not thread.is_alive()

def test_browser_real_component_and_http_memory_roundtrip(fixture_server):
    url,r,c,records,recalls=fixture_server
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport={'width':1200,'height':1500});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(url);page.get_by_label('Địa chỉ Cognee',exact=True).fill(url);page.get_by_label('API key',exact=True).fill('fixture-http-key')
        page.get_by_role('button',name='Kiểm tra và lưu kết nối').click();expect(page.get_by_role('status')).to_contain_text('Đã xác minh')
        expect(page.get_by_label('API key',exact=True)).to_have_value('')
        page.get_by_label('Brain lưu hội thoại',exact=True).select_option(BRAIN)
        assert page.locator('option[value="'+OTHER+'"]').is_disabled()
        page.get_by_label('Tra cứu conversation',exact=True).check();page.get_by_label('Tự lưu hội thoại mới',exact=True).check();page.get_by_label('Tra cứu trước mỗi câu hỏi',exact=True).check();page.get_by_label('Đồng ý phạm vi lưu và chia sẻ',exact=True).check()
        page.get_by_role('button',name='Lưu lựa chọn Brain').click();expect(page.get_by_role('status')).to_contain_text('Đã lưu lựa chọn')
        page.get_by_label('Đồng ý thay memory provider',exact=True).check();page.get_by_role('button',name='Bật Cognee Memory',exact=True).click();expect(page.get_by_role('status')).to_contain_text('Đã lưu provider')
        assert c.cfg['memory']['provider']==ID
        provider=importlib.import_module('forkplugin.provider').RemoteMemoryProvider(r,background=False);provider.initialize('fixture-session',hermes_home=str(r.home))
        provider.sync_turn('Nhớ nội dung fixture tiếng Việt.','Đã ghi nhận fixture.');status=provider.outbox.flush(r)
        assert status['indexed']==1 and len(records)==1
        packet=json.loads(records[0]['raw']);original=json.loads(packet['source_text']);assert original['completed_turn']['user']=='Nhớ nội dung fixture tiếng Việt.'
        result=json.loads(provider.handle_tool_call('cognee_recall',{'query':'fixture'}));assert result['ok'] and result['results'][0]['brain_id']==BRAIN
        assert all(x['searchType']=='HYBRID_COMPLETION' and x['onlyContext'] and x['datasetIds']==[BRAIN] and 'session_id' not in x for x in recalls)
        page.get_by_role('button',name='Tải lại danh mục Brain').click();expect(page.get_by_role('status')).to_contain_text('Đã tải danh mục')
        page.screenshot(path=str(ROOT/'evidence/23-ui-http-fixture.png'),full_page=True)
        page.get_by_label('API key',exact=True).fill('fixture-unsent-value');page.evaluate('fixtureSwitchProfile()');expect(page.get_by_label('API key',exact=True)).to_have_value('')
        assert not errors;provider.shutdown();browser.close()
        (ROOT/'evidence/23-browser-http.json').write_text(json.dumps({'scope':'real Edge + real HTTP + real plugin component/API/provider; synthetic Cognee fixture and SDK adapter, NOT real Cognee/ACL/LLM/native Electron acceptance','page_errors':errors,'records_raw_verified':len(records),'recall_requests':len(recalls),'profile_remount_cleared_input':True,'all_memory_wire_contracts_verified':True},ensure_ascii=False,indent=2),encoding='utf-8')
