import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import sys,struct,zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from viewport_evidence_gate import validate_viewpoints

def chunk(k,v):
    d=k+v
    return struct.pack(">I",len(v))+d+struct.pack(">I",zlib.crc32(d))

def png(rgb):
    header=struct.pack(">IIBBBBB",4,4,8,2,0,0,0)
    rows=b"".join(b"\x00"+bytes(rgb)*4 for _ in range(4))
    return b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",header)+chunk(b"IDAT",zlib.compress(rows))+chunk(b"IEND",b"")

class ViewportTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.a=Path(self.temp.name)/"a.png"
        self.b=Path(self.temp.name)/"b.png"
        self.a.write_bytes(png((1,20,70)))
        self.b.write_bytes(png((30,40,50)))
    def tearDown(self):
        self.temp.cleanup()
    def validate(self):
        return validate_viewpoints([self.a,self.b],4,4,20)
    def test_distinct(self):
        self.assertEqual(self.validate(),[])
    def test_duplicate(self):
        self.b.write_bytes(self.a.read_bytes())
        self.assertTrue(any("duplicate" in x for x in self.validate()))
    def test_missing(self):
        self.b.unlink()
        self.assertTrue(any("not readable" in x for x in self.validate()))
    def test_bad_header(self):
        self.a.write_bytes(b"bad")
        self.assertTrue(any("invalid PNG" in x for x in self.validate()))
    def test_low_resolution(self):
        self.assertTrue(any("inadequate" in x for x in validate_viewpoints([self.a,self.b],1280,720,20)))

if __name__=="__main__":
    unittest.main()
