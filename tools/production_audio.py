"""Inspect the exact PCM bank prepared by a project; no inferred acoustic/art approval."""
import hashlib,math,struct,wave
from pathlib import Path
try:
 from tools.production_assets import local
except ModuleNotFoundError:
 from production_assets import local

def validate(project,record,directory):
 root=Path(project).resolve();base=local(root,directory)
 if record.get('version')!=1 or not isinstance(record.get('banks'),dict) or not record['banks']:raise ValueError('explicit audio bank version 1 required')
 for field,parent in [('source_hashes',root),('output_hashes',base)]:
  values=record.get(field)
  if not isinstance(values,dict) or not values:raise ValueError('source and output hashes required')
  total=0
  for name,sha in values.items():
   p=local(parent,name);size=p.stat().st_size;total+=size
   if size<=0 or total>64*1024*1024:raise ValueError('audio inspection exceeds 64 MiB')
   h=hashlib.sha256()
   with p.open('rb') as f:
    for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
   if h.hexdigest()!=sha:raise ValueError('audio hash mismatch: '+name)
 references=[]
 for category,files in record['banks'].items():
  if not category or not isinstance(files,list) or not files or len(files)>16 or len(set(files))!=len(files):raise ValueError('unique bounded audio variants required')
  references.extend(files)
 if set(references)!=set(record['output_hashes']):raise ValueError('audio bank and delivered output closure differ')
 clips=[]
 for name in sorted(set(references)):
  path=local(base,name)
  if path.suffix!='.wav':raise ValueError('native inspection expects PCM WAV')
  with wave.open(str(path)) as w:
   if w.getsampwidth()!=2 or w.getnchannels() not in (1,2) or w.getframerate() not in (22050,44100,48000):raise ValueError('supported 16-bit PCM format required')
   data=w.readframes(w.getnframes());values=[x[0]/32768 for x in struct.iter_unpack('<h',data)]
   if not values:raise ValueError('empty PCM stream')
   peak=max(map(abs,values));rms=math.sqrt(sum(x*x for x in values)/len(values))
   if peak>=.999 or rms<.0001:raise ValueError('clipped or effectively silent PCM clip: '+name)
   clips.append({'file':name,'seconds':w.getnframes()/w.getframerate(),'peak_dbfs':20*math.log10(peak),'rms_dbfs':20*math.log10(rms)})
 return {'ok':True,'banks':len(record['banks']),'clips':clips,'limits':['PCM/hash validation does not approve the sound design, spatial mix or audio device latency.','Native playback/event routing and human review are required.']}
