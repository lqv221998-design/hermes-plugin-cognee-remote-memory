import importlib,json
from test_remote import UID,BRAIN

def cls():
    m=importlib.import_module('forkplugin.remote')
    assert callable(getattr(m,'Outbox',None)),'Durable conversation outbox missing'
    return m.Outbox

def test_outbox_survives_restart_and_deduplicates_same_snapshot(tmp_path):
    binding={'endpoint':'https://cognee.example','expected_user_id':UID,'expected_tenant_id':'','write_brain':BRAIN,'device_id':'test-device'}
    payload={'schema':'hermes-conversation-v1','session_id':'s1','messages':[{'role':'user','content':'Nhớ tiếng Việt 🏗️'},{'role':'assistant','content':'Đã ghi nhận.'}]}
    box=cls()(tmp_path/'outbox.sqlite3');rid=box.enqueue(binding,payload)
    assert rid==box.enqueue(binding,payload)
    restored=cls()(tmp_path/'outbox.sqlite3')
    assert restored.status()['queued']==1
    row=restored.next_queued()
    assert row['binding']==binding
    decoded=json.loads(row['payload']);assert decoded['source_text']==json.dumps(payload,ensure_ascii=False,separators=(',',':'))
    assert row['id']==rid+':1'

def test_uncertain_write_is_not_resent_on_restart(tmp_path):
    from test_runtime import make,DirectoryClient
    r,c=make(tmp_path);r.connect({'endpoint':'https://cognee.example','api_key':'fixture-key'})
    r.save_selection({'write_brain':BRAIN,'read_brains':[BRAIN],'capture':True,'auto_recall':True,'acknowledge_sharing':True})
    box=cls()(tmp_path/'outbox.sqlite3');box.enqueue(r.settings(),{'session_id':'s','messages':[{'role':'user','content':'q'}]})
    assert callable(getattr(box,'flush',None)),'Delivery/reconciliation missing'
    calls=[]
    class LostResponse(DirectoryClient):
        def send_packet(self,*args):calls.append(args);raise TimeoutError('response lost')
        def find_packet(self,*args):return None
    r.backend_factory=LostResponse;box.flush(r)
    assert box.status()['uncertain']==1 and len(calls)==1
    cls()(tmp_path/'outbox.sqlite3').flush(r)
    assert len(calls)==1

def test_packet_raw_verification_required_before_indexed(tmp_path):
    from test_runtime import make,DirectoryClient
    r,c=make(tmp_path);r.connect({'endpoint':'https://cognee.example','api_key':'fixture-key'})
    r.save_selection({'write_brain':BRAIN,'read_brains':[BRAIN],'capture':True,'auto_recall':True,'acknowledge_sharing':True})
    box=cls()(tmp_path/'outbox.sqlite3');box.enqueue(r.settings(),{'session_id':'s','messages':[{'role':'user','content':'q'}]})
    assert callable(getattr(box,'flush',None)),'Delivery/reconciliation missing'
    class Packet(DirectoryClient):
        def send_packet(self,*args):return {'dataset_id':BRAIN,'status':'completed'}
        def find_packet(self,dataset,record_id,expected):return {'data_id':'33333333-3333-4333-8333-333333333333','sha256':__import__('hashlib').sha256(expected.encode()).hexdigest()}
    r.backend_factory=Packet;box.flush(r)
    assert box.status()['indexed']==1

def test_large_transcript_splits_losslessly(tmp_path):
    payload={'session_id':'s','messages':[{'role':'user','content':'Tiếng Việt 🏗️ '*18000}]}
    box=cls()(tmp_path/'outbox.sqlite3');box.enqueue({},payload)
    with box.db() as db:rows=[box.decode(row) for row in db.execute('SELECT * FROM events')]
    parts=sorted((json.loads(x['payload']) for x in rows),key=lambda x:x['part_index'])
    assert len(parts)>1 and all(x['part_total']==len(parts) for x in parts)
    assert json.loads(''.join(x['source_text'] for x in parts))==payload
