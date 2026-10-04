import hashlib,json,tempfile,unittest,wave
from unittest.mock import patch
from pathlib import Path
from tools.production_audio import validate
class AudioTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  self.bank=self.root/'assets/audio';self.bank.mkdir(parents=True)
  self.source=self.root/'source.txt';self.source.write_text('source provenance fixture')
  self.clip=self.bank/'clip.wav'
  self.write(2000)
 def write(self,amplitude):
  with wave.open(str(self.clip),'wb') as w:
   w.setnchannels(1);w.setsampwidth(2);w.setframerate(22050);w.writeframes(int(amplitude).to_bytes(2,'little',signed=True)*500)
 def record(self):return {'version':1,'banks':{'step':['clip.wav']},'source_hashes':{'source.txt':hashlib.sha256(self.source.read_bytes()).hexdigest()},'output_hashes':{'clip.wav':hashlib.sha256(self.clip.read_bytes()).hexdigest()}}
 def test_native_bank_provenance_and_pcm(self):
  r=validate(self.root,self.record(),'assets/audio');self.assertTrue(r['ok']);self.assertEqual(len(r['clips']),1)
 def test_changed_source_rejected(self):
  r=self.record();self.source.write_text('changed')
  with self.assertRaises(ValueError):validate(self.root,r,'assets/audio')
 def test_undeclared_bank_member_rejected(self):
  r=self.record();r['banks']['step'].append('other.wav')
  with self.assertRaises(ValueError):validate(self.root,r,'assets/audio')
 def test_clipped_or_silent_pcm_rejected(self):
  for amplitude in (32767,0):
   self.write(amplitude)
   with self.assertRaises(ValueError):validate(self.root,self.record(),'assets/audio')

 def test_truncated_payload_and_parser_failures_rejected(self):
  data=self.clip.read_bytes()
  for corrupt in (data[:46],data[:45],b'nope'):
   self.clip.write_bytes(corrupt)
   with self.assertRaises(ValueError):validate(self.root,self.record(),'assets/audio')

 def test_diagnostics_use_hash_verified_snapshot(self):
  record=self.record();original_open=wave.open
  def replace_then_open(snapshot,mode):
   self.clip.write_bytes(b'replaced after hash check')
   return original_open(snapshot,mode)
  with patch('tools.production_audio.wave.open',side_effect=replace_then_open):
   result=validate(self.root,record,'assets/audio')
  self.assertAlmostEqual(result['clips'][0]['peak_dbfs'],-24.2883987859)

 def test_bounded_chunk_diagnostics(self):
  with wave.open(str(self.clip),'wb') as w:
   w.setnchannels(2);w.setsampwidth(2);w.setframerate(48000)
   w.writeframes((2000).to_bytes(2,'little',signed=True)*2*100000)
  result=validate(self.root,self.record(),'assets/audio')
  self.assertAlmostEqual(result['clips'][0]['seconds'],100000/48000)
