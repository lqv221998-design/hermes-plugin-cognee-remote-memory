import importlib,json
from test_runtime import make,DirectoryClient
from test_remote import BRAIN

def provider(runtime):
    import forkplugin
    assert __import__('pathlib').Path(forkplugin.__path__[0],'provider.py').exists(),'Remote memory provider missing'
    return importlib.import_module('forkplugin.provider').RemoteMemoryProvider(runtime,background=False)

def setup(tmp_path):
    r,c=make(tmp_path);r.connect({'endpoint':'https://cognee.example','api_key':'fixture-key'})
    r.save_selection({'write_brain':BRAIN,'read_brains':[BRAIN],'capture':True,'auto_recall':True,'acknowledge_sharing':True})
    c.cfg['memory']['provider']='cognee-remote-memory'
    class Evidence(DirectoryClient):
        def recall(self,**kwargs):self.last=kwargs;return [{'text':'bằng chứng gốc','references':[{'data_id':BRAIN}]}]
    r.backend_factory=Evidence
    return r,c,provider(r)

def test_complete_visible_messages_captured_but_not_system_tools_or_secrets(tmp_path):
    r,c,p=setup(tmp_path);p.initialize('session-a',hermes_home=str(tmp_path))
    messages=[{'role':'system','content':'system private'},{'role':'user','content':'Câu hỏi'},{'role':'assistant','content':'Đang kiểm tra'},{'role':'tool','content':'tool private'},{'role':'assistant','content':'API_KEY=fixture-secret-value'}]
    p.sync_turn('Câu hỏi','Kết luận',session_id='session-a',messages=messages)
    row=p.outbox.next_queued();packet=json.loads(row['payload']);source=json.loads(packet['source_text'])
    text=json.dumps(source,ensure_ascii=False)
    assert 'Đang kiểm tra' in text and 'Câu hỏi' in text
    assert 'system private' not in text and 'tool private' not in text and 'fixture-secret-value' not in text
    assert '[REDACTED]' in text

def test_explicit_and_prefetch_recall_use_only_selected_brain(tmp_path):
    r,c,p=setup(tmp_path);p.initialize('a',hermes_home=str(tmp_path))
    output=json.loads(p.handle_tool_call('cognee_recall',{'query':'Nghiệm thu?'}))
    assert output['results'][0]['brain_id']==BRAIN and output['search_type']=='HYBRID_COMPLETION'
    p.queue_prefetch('Nghiệm thu?',session_id='a');assert 'bằng chứng gốc' in p.prefetch('Nghiệm thu?',session_id='a')
    p.on_session_switch('b',reset=True)
    class FreshSessionEvidence(DirectoryClient):
        def recall(self,**kwargs):return [{'text':'bằng chứng mới sau chuyển phiên','references':[]}]
    r.backend_factory=FreshSessionEvidence
    fresh=p.prefetch('Nghiệm thu?',session_id='b')
    assert 'bằng chứng mới sau chuyển phiên' in fresh and 'bằng chứng gốc' not in fresh

def test_subagent_does_not_capture(tmp_path):
    r,c,p=setup(tmp_path);p.initialize('a',hermes_home=str(tmp_path),agent_context='subagent')
    p.sync_turn('q','a');assert p.outbox.status()['queued']==0
