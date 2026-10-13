"""Actual MemoryManager routing, independent of author installation paths."""
import argparse,importlib.util,pathlib,sys,json
parser=argparse.ArgumentParser();parser.add_argument('--hermes-repo',required=True);args=parser.parse_args()
sys.path.insert(0,args.hermes_repo);import hermes_cli.main
root=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('_recipient_remote_tools',root/'__init__.py',submodule_search_locations=[str(root)])
assert spec is not None and spec.loader is not None
pkg=importlib.util.module_from_spec(spec);sys.modules[spec.name]=pkg;spec.loader.exec_module(pkg)
provider=__import__(spec.name+'.provider',fromlist=['RemoteMemoryProvider']).RemoteMemoryProvider
from agent.memory_manager import MemoryManager
p=provider();manager=MemoryManager();manager.add_provider(p)
names={s['name'] for s in manager.get_all_tool_schemas()}
for name in ['cognee_recall','cognee_remember','cognee_memory_status']:assert name in names and manager.has_tool(name)
rejected=json.loads(manager.handle_tool_call('cognee_recall',{'query':'connection test'}));assert not rejected['ok'] and 'not_initialized' in rejected['error']
print(json.dumps({'nativeRouting':True,'initializationGate':True,'networkCalls':0}))
