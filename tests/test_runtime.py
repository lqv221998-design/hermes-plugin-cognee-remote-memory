import importlib,json
from test_remote import UID,BRAIN,OTHER
ID='cognee-remote-memory'
class DirectoryClient:
    def __init__(self,origin,read_key):self.origin=origin;self.read_key=read_key
    def probe(self):
        assert self.read_key()=='fixture-key'
        return {'identity':{'id':UID,'tenant_id':''},'brains':[{'id':BRAIN,'name':'conversation','permissions':['read','write'],'protected':False},{'id':OTHER,'name':'qaqc_company_standard','permissions':['read','write'],'protected':True}]}
class MemoryConfig:
    def __init__(self):self.cfg={'plugins':{'enabled':[ID],'entries':{}},'memory':{'provider':'hindsight'},'keep':'unchanged'};self.key=''
    def read(self):return json.loads(json.dumps(self.cfg))
    def write(self,c):self.cfg=c

def make(tmp_path):
    m=importlib.import_module('forkplugin.remote')
    assert callable(getattr(m,'Runtime',None)),'Profile-scoped connection runtime missing'
    c=MemoryConfig();r=m.Runtime(tmp_path,c.read,c.write,lambda:c.key,lambda k:setattr(c,'key',k),backend_factory=DirectoryClient)
    return r,c

def test_connect_pins_identity_without_activating_provider(tmp_path):
    r,c=make(tmp_path);out=r.connect({'endpoint':'https://cognee.example','api_key':'fixture-key'})
    assert out['identity']=={'id':UID,'tenant_id':''}
    assert c.cfg['memory']['provider']=='hindsight' and c.cfg['keep']=='unchanged'
    assert r.public()['has_api_key'] and 'fixture-key' not in json.dumps(r.public())
    assert r.public()['capture'] is False

def test_selections_narrow_acl_and_protect_standards(tmp_path):
    import pytest
    r,c=make(tmp_path);r.connect({'endpoint':'https://cognee.example','api_key':'fixture-key'})
    with pytest.raises(ValueError):r.save_selection({'write_brain':OTHER,'read_brains':[BRAIN],'capture':True,'auto_recall':True,'acknowledge_sharing':True})
    r.save_selection({'write_brain':BRAIN,'read_brains':[OTHER],'capture':True,'auto_recall':True,'acknowledge_sharing':True})
    assert r.public()['write_brain']==BRAIN and r.public()['read_brains']==[OTHER]

def test_blank_key_does_not_cross_origin(tmp_path):
    import pytest
    r,c=make(tmp_path);r.connect({'endpoint':'https://cognee.example','api_key':'fixture-key'})
    with pytest.raises(ValueError):r.connect({'endpoint':'https://other.example','api_key':''})
