import pathlib,importlib.util,hashlib
from test_remote import ROOT

def test_installer_is_plan_only_and_refuses_overwrite(tmp_path):
    path=ROOT/'install.py';assert path.exists(),'Safe recipient installer missing'
    spec=importlib.util.spec_from_file_location('install_fork',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    home=tmp_path/'hermes-home';home.mkdir();(home/'config.yaml').write_text('memory:\n  provider: hindsight\n',encoding='utf-8');before=(home/'config.yaml').read_bytes()
    plan=module.install(ROOT,home,apply=False)
    assert not pathlib.Path(plan['target']).exists()
    result=module.install(ROOT,home,apply=True)
    assert result['applied'] and (home/'config.yaml').read_bytes()==before
    for p in ROOT.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':assert (pathlib.Path(result['target'])/p.relative_to(ROOT)).read_bytes()==p.read_bytes()
    import pytest
    with pytest.raises(FileExistsError):module.install(ROOT,home,apply=True)
