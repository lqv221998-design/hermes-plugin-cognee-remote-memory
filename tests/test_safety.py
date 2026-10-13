import json,pytest,os
from test_runtime import make,DirectoryClient,ID
from test_remote import UID,BRAIN,OTHER,backend,Wire
from test_provider import setup

def test_identity_change_is_rejected(tmp_path):
    r,c=make(tmp_path);r.connect({'endpoint':'https://cognee.example','api_key':'fixture-key'})
    class Changed(DirectoryClient):
        def probe(self):out=super().probe();out['identity']['id']=OTHER;return out
    r.backend_factory=Changed
    with pytest.raises(ValueError):r.client()

def test_profile_change_fails_closed(tmp_path):
    r,c=make(tmp_path);r.connect({'endpoint':'https://cognee.example','api_key':'fixture-key'});r.current_home=lambda:tmp_path/'different-home'
    with pytest.raises(ValueError):r.public()
    with pytest.raises(ValueError):r.client()

def test_uncertain_queue_reconciles_read_only_without_resend(tmp_path):
    from test_outbox import cls
    r,c=make(tmp_path);r.connect({'endpoint':'https://cognee.example','api_key':'fixture-key'});r.save_selection({'write_brain':BRAIN,'read_brains':[BRAIN],'capture':True,'auto_recall':True,'acknowledge_sharing':True})
    b=cls()(tmp_path/'q.sqlite3');b.enqueue(r.settings(),{'messages':[{'role':'user','content':'original'}]});row=b.next_queued();b.mark(row['id'],'uncertain');calls=[]
    class Reconcile(DirectoryClient):
        def find_packet(self,*args):calls.append('read');return {'data_id':OTHER,'sha256':__import__('hashlib').sha256(args[2].encode()).hexdigest()}
        def send_packet(self,*args):raise AssertionError('Never resend uncertain')
    r.backend_factory=Reconcile;b.reconcile(r)
    assert calls==['read'] and b.status()['raw_verified']==1
    b.flush(r);assert calls==['read']

def test_revoked_write_acl_preserves_queued_without_post(tmp_path):
    from test_outbox import cls
    r,c=make(tmp_path);r.connect({'endpoint':'https://cognee.example','api_key':'fixture-key'});r.save_selection({'write_brain':BRAIN,'read_brains':[BRAIN],'capture':True,'auto_recall':True,'acknowledge_sharing':True})
    b=cls()(tmp_path/'q.sqlite3');b.enqueue(r.settings(),{'messages':[{'role':'user','content':'q'}]})
    class Reader(DirectoryClient):
        def probe(self):out=super().probe();out['brains'][0]['permissions']=['read'];return out
        def send_packet(self,*args):raise AssertionError('Write ACL revoked')
    r.backend_factory=Reader;b.flush(r);assert b.status()['queued']==1 and b.status()['indexed']==0

def test_activation_refuses_duplicate_cognee_writer(tmp_path):
    r,c=make(tmp_path);r.connect({'endpoint':'https://cognee.example','api_key':'fixture-key'});r.save_selection({'write_brain':BRAIN,'read_brains':[BRAIN],'capture':True,'auto_recall':True,'acknowledge_sharing':True})
    c.cfg['plugins']['enabled'].append('cognee-admin')
    with pytest.raises(ValueError):r.activate({'acknowledge_replace':True})
    assert c.cfg['memory']['provider']=='hindsight'

@pytest.mark.parametrize('value',['ABCDEFAB-ABCD-ABCD-ABCD-ABCDEFABCDEF','bad',[],None])
def test_malformed_scope_never_sent(value):
    w=Wire();c=backend(w)
    with pytest.raises((ValueError,TypeError)):c.recall(query='q',datasets=[value])
    assert not w.requests

def test_positional_repeated_text_not_summarized(tmp_path):
    r,c,p=setup(tmp_path);p.initialize('a',hermes_home=str(tmp_path))
    p.sync_turn('same','reply',messages=[{'role':'user','content':'same'},{'role':'assistant','content':'reply'},{'role':'user','content':'same'},{'role':'assistant','content':'reply'}])
    source=json.loads(json.loads(p.outbox.next_queued()['payload'])['source_text'])
    assert len(source['messages'])==4

def test_windows_queue_does_not_store_plaintext(tmp_path):
    from test_outbox import cls
    if os.name!='nt':pytest.skip('Windows DPAPI-only assertion')
    b=cls()(tmp_path/'encrypted.sqlite3');b.enqueue({}, {'text':'private-fixture-unique-12345'})
    assert b'private-fixture-unique-12345' not in (tmp_path/'encrypted.sqlite3').read_bytes()

def test_changed_selection_does_not_inject_old_prefetch(tmp_path):
    r,c,p=setup(tmp_path);p.initialize('a',hermes_home=str(tmp_path));p.queue_prefetch('q',session_id='a')
    value=r.settings();value['read_brains']=[OTHER];r.save(value)
    assert p.prefetch('q',session_id='a')==''

def test_revoked_read_acl_does_not_inject_cached_evidence(tmp_path):
    r,c,p=setup(tmp_path);p.initialize('a',hermes_home=str(tmp_path));p.queue_prefetch('q',session_id='a')
    class Revoked(DirectoryClient):
        def probe(self):out=super().probe();out['brains']=[];return out
    r.backend_factory=Revoked
    assert p.prefetch('q',session_id='a')==''

def test_fork_does_not_use_upstream_shared_configuration_or_backup_roots(tmp_path):
    r,c,p=setup(tmp_path)
    with pytest.raises(ValueError):p.save_config({'service_url':'https://other.example'},str(tmp_path))
    assert not (tmp_path/'cognee.json').exists()
    assert p.backup_paths()==[]

def test_identity_signature_changes_when_connection_binding_changes(tmp_path):
    r,c,p=setup(tmp_path);before=p.identity_signature();s=r.settings();s['expected_user_id']=OTHER;r.save(s)
    assert p.identity_signature()!=before
