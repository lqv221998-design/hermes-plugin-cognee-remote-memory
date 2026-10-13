"""Safe drop-in installer. Explicit home, plan-only default, never overwrite/activate."""
import argparse,hashlib,json,shutil
from pathlib import Path
ID='cognee-remote-memory'
def install(source,home,*,apply=False):
    source=Path(source).resolve();home=Path(home)
    if not home.is_absolute():raise ValueError('Require an explicit absolute Hermes home.')
    home=home.resolve();target=home/'plugins'/ID
    if not (source/'plugin.yaml').is_file():raise ValueError('Source package missing.')
    if target.exists():raise FileExistsError('Existing plugin retained; choose a new test home or reviewed upgrade.')
    files=[p for p in sorted(source.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']
    if any(p.name in {'.env','config.yaml','auth.json','outbox.sqlite3'} or p.is_symlink() for p in files):raise ValueError('Runtime credentials/state or symlink in source.')
    result={'plugin':ID,'target':str(target),'files':len(files),'applied':apply,'config_changed':False,'credentials_copied':False,'enabled':False,'memory_activated':False}
    if apply:
        target.mkdir(parents=True,exist_ok=False)
        for p in files:
            out=target/p.relative_to(source);out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
            if out.read_bytes()!=p.read_bytes():raise OSError('Install read-back mismatch; do not enable incomplete copy.')
        result['all_code_bytes_verified']=True
    return result
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--home',required=True);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    print(json.dumps(install(Path(__file__).parent,Path(args.home),apply=args.apply),ensure_ascii=False,indent=2))
