from test_provider import provider
from test_runtime import make


def test_provider_tool_schemas_exist_before_host_initialization(tmp_path):
    runtime,_=make(tmp_path)
    memory=provider(runtime)
    schemas=memory.get_tool_schemas()
    assert {s['name'] for s in schemas} == {
        'cognee_recall','cognee_remember','cognee_memory_status'
    }
    assert not memory._initialized
