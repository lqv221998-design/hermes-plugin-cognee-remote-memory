import pathlib
from test_remote import PLUGIN

def test_desktop_component_ships_real_connection_and_brain_controls():
    path=PLUGIN/'desktop/plugin.js'
    assert path.exists(),'Desktop connection component missing'
    source=path.read_text(encoding='utf-8')
    assert "ctx.rest('/connect'" in source and "ctx.rest('/selection'" in source
    assert 'HYBRID_COMPLETION' in source and "type:'password'" in source
