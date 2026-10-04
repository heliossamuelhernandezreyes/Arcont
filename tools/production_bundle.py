"""Relocate hash-verified native candidates; publish with an atomic Linux rename."""
from __future__ import annotations
import ctypes,errno,hashlib,json,os,sys
from pathlib import Path,PurePosixPath
import re,shutil,tempfile

MAX_BYTES=512*1024*1024
SUFFIXES={'.tscn','.tres','.res','.exr','.png','.lmbake'}

def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def relative(value):
 if not isinstance(value,str):raise ValueError('safe relative path required')
 path=PurePosixPath(value)
 if not value or value!=path.as_posix() or path.is_absolute() or '..' in path.parts or '\\' in value or path.as_posix()=='.':raise ValueError('safe relative path required')
 return Path(*path.parts)

def safe_path(project,path):
 if project not in path.resolve().parents or any(p.is_symlink() for p in [path,*path.parents] if project==p or project in p.parents):raise ValueError('symlink or escaped project path')

def read_artifact(path,size,sha):
 # Hash exactly the bounded bytes that will be published, not an earlier read.
 with path.open('rb') as f:data=f.read(size+1)
 if len(data)!=size or hashlib.sha256(data).hexdigest()!=sha:raise ValueError('artifact changed during publication: '+str(path))
 return data

def managed(target,destination):
 marker=target/'arcont-bundle.json'
 if marker.is_symlink() or not marker.is_file():raise ValueError('refusing to replace an unmanaged asset directory')
 try:receipt=json.loads(marker.read_text())
 except (OSError,ValueError):raise ValueError('invalid bundle receipt')
 if receipt.get('owner')!='arcont-native-bundle' or receipt.get('destination')!=destination:raise ValueError('receipt does not identify this destination')
 files=receipt.get('output_hashes')
 if not isinstance(files,dict) or not files:raise ValueError('missing recorded bundle contents')
 expected=set(files)|{'arcont-bundle.json'}
 actual={p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file() or p.is_symlink()}
 if actual!=expected:raise ValueError('bundle contains unrecorded or missing assets')
 for name,sha in files.items():
  path=target/relative(name)
  if any(p.is_symlink() for p in [path,*path.parents] if p==target or target in p.parents) or not path.is_file() or digest(path)!=sha:raise ValueError('managed bundle was modified: '+name)
 return receipt

def atomic_publish(candidate,target,replace):
 # A missing renameat2 is an explicit failure, preserving the old destination.
 # No two-rename emulation: it would expose an absent bundle after a process crash.
 if sys.platform!='linux':raise ValueError('atomic native bundle publication currently requires Linux renameat2')
 libc=ctypes.CDLL(None,use_errno=True)
 try:rename=libc.renameat2
 except AttributeError:raise ValueError('atomic renameat2 is unavailable')
 rename.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint]
 rename.restype=ctypes.c_int
 flags=2 if replace else 1 # RENAME_EXCHANGE / RENAME_NOREPLACE
 if rename(-100,os.fsencode(candidate),-100,os.fsencode(target),flags)!=0:
  error=ctypes.get_errno()
  if error in (errno.EEXIST,errno.ENOTEMPTY):raise ValueError('destination appeared during publication; replacement was not authorized')
  raise OSError(error,os.strerror(error))

def materialize(project,source,destination,files,replace=False):
 project=Path(project).resolve();source_path=relative(source);target_path=relative(destination)
 if source_path.parts[:2]!=('.arcont','runs') or target_path.parts[0]!='assets' or len(target_path.parts)<2:raise ValueError('a native candidate under .arcont/runs and a game asset destination are required')
 src=project/source_path;target=project/target_path
 for path in [src,target]:safe_path(project,path)
 if not isinstance(files,dict) or not files or len(files)>5000:raise ValueError('explicit non-empty artifact hashes required')
 checked=[];total=0
 for name,sha in files.items():
  path=src/relative(name);safe_path(project,path)
  if path.suffix not in SUFFIXES:raise ValueError('unsupported scene artifact: '+name)
  if not isinstance(sha,str) or not re.fullmatch('[0-9a-f]{64}',sha):raise ValueError('invalid artifact hash')
  if not path.is_file():raise ValueError('missing artifact: '+name)
  size=path.stat().st_size;total+=size
  if size<=0 or total>MAX_BYTES:raise ValueError('empty artifact or scene bundle exceeds 512 MiB')
  checked.append((name,path,size,sha))
 target.parent.mkdir(parents=True,exist_ok=True)
 # All publishers using this protocol serialize verification and commit per project.
 # The atomic rename additionally protects non-replace against external publishers.
 from fcntl import flock,LOCK_EX,LOCK_UN
 lock_path=project/'.arcont/native-bundle.lock';lock_path.parent.mkdir(parents=True,exist_ok=True);safe_path(project,lock_path)
 with lock_path.open('a+b') as lock:
  flock(lock,LOCK_EX)
  candidate=None
  try:
   previous=None
   if target.exists():
    if not replace:raise ValueError('refusing to replace an existing asset directory')
    previous=managed(target,target_path.as_posix())
   source_prefix='res://'+source_path.as_posix()+'/';target_prefix='res://'+target_path.as_posix()+'/'
   candidate=Path(tempfile.mkdtemp(prefix='.arcont-bundle-',dir=target.parent));output={}
   for name,path,size,sha in checked:
    data=read_artifact(path,size,sha)
    if path.suffix in ('.tscn','.tres'):
     text=data.decode('utf-8').replace(source_prefix,target_prefix)
     text=re.sub(r'(\[ext_resource[^\n]*) uid="uid://[^"]+"',r'\1',text)
     if 'res://.arcont/runs/' in text:raise ValueError('reference to another unpublished bundle')
     data=text.encode('utf-8')
    elif source_prefix.encode() in data or b'res://.arcont/runs/' in data:raise ValueError('binary references require native reserialization before relocation')
    out=candidate/relative(name);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data);output[name]=hashlib.sha256(data).hexdigest()
   receipt={'version':1,'owner':'arcont-native-bundle','source':source_path.as_posix(),'destination':target_path.as_posix(),'source_hashes':files,'output_hashes':output,'limits':['Opaque binary resources are copied unchanged; compressed external references are not inspected.','Native scene reopen and export validation are required.','Atomic namespace publication on Linux; filesystem durability after power loss is not established.','Artifact integrity is not visual quality or handset performance approval.']}
   (candidate/'arcont-bundle.json').write_text(json.dumps(receipt,indent=2)+'\n')
   if previous is not None and managed(target,target_path.as_posix())!=previous:raise ValueError('destination changed before publication')
   atomic_publish(candidate,target,previous is not None)
   return {'ok':True,'files':len(output),'destination':destination,'receipt':str(target/'arcont-bundle.json'),'native_reopen_required':True}
  finally:
   if candidate is not None and candidate.exists():shutil.rmtree(candidate)
   flock(lock,LOCK_UN)
