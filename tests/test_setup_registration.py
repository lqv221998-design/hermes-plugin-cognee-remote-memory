"""Registration publishes onboarding without network/install/config work."""
import importlib.util,sys,pathlib

def test_setup_and_using_skills_registered_with_existing_provider():
 root=pathlib.Path(__file__).resolve().parents[1]
 spec=importlib.util.spec_from_file_location('portable_registration',root/'__init__.py',submodule_search_locations=[str(root)])
 assert spec is not None and spec.loader is not None
 module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
 class Context:
  def __init__(self):self.providers=[];self.skills={}
  def register_memory_provider(self,provider):self.providers.append(provider)
  def register_skill(self,name,path,**kwargs):self.skills[name]=pathlib.Path(path)
 ctx=Context();module.register(ctx)
 assert len(ctx.providers)==1 and ctx.providers[0].name=='cognee-remote-memory'
 assert set(ctx.skills)=={'setup','using'}
 assert all(p.is_file() for p in ctx.skills.values())
 assert 'cognee-remote-memory:setup' in ctx.providers[0].unavailable_reason()
