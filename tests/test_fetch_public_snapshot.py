import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

path=Path(__file__).resolve().parents[1]/'scripts/fetch_public_snapshot.py'
if not path.is_file():path=Path(__file__).with_name('fetch_public_snapshot.py')
spec=importlib.util.spec_from_file_location('public_fetch',path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class Reader:
    def __init__(self,payload=b'package'):
        self.payload=payload;self.calls=0;self.channel='community'
    def json(self,path,params=()):
        if path=='materials/catalog':return {'total_count':1,'materials':[{
            'material_id':'mat_one','revision_id':'rev_one','content_hash':'sha256:'+'a'*64,
            'channel':self.channel,'package_url':'/api/material-registry/v1/packages/one.zip',
            'package_sha256':hashlib.sha256(b'package').hexdigest(),'package_bytes':7,'display':{}}]}
        if path=='luts/catalog':return {'total_count':0,'items':[]}
        return {'subject':None,'items':[{'resource_id':'mat_one','likes':2,'saves':3,'downloads':4,
            'liked':False,'saved':False,'revisions':[{'revision_id':'rev_one','content_hash':'sha256:'+'a'*64}]}]}
    def bytes(self,*args):
        self.calls+=1
        return self.payload


class PublicFetchTests(unittest.TestCase):
    def test_unchanged_packages_are_reused_and_personal_state_is_not_exported(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);license_file=root/'DATA-LICENSE.md';license_file.write_text('Terms')
            reader=Reader();first=root/'first'
            module.collect(reader,first,root/'empty',license_file)
            self.assertEqual(reader.calls,1)
            stats=json.loads((first/'materials/activity.json').read_text())['items'][0]
            self.assertNotIn('liked',stats);self.assertNotIn('saved',stats)
            self.assertEqual(stats['likes'],2)
            reader=Reader();report=module.collect(reader,root/'second',first,license_file)
            self.assertEqual(reader.calls,0);self.assertEqual(report['reused_packages'],1)
            self.assertEqual((first/'materials/catalog.json').read_bytes(),(root/'second/materials/catalog.json').read_bytes())

    def test_bad_package_and_private_channel_leave_no_published_metadata(self):
        for private in (False,True):
            with self.subTest(private=private),tempfile.TemporaryDirectory() as folder:
                root=Path(folder);license_file=root/'license';license_file.write_text('Terms')
                reader=Reader(b'bad');reader.channel='team' if private else 'community'
                with self.assertRaises(ValueError):module.collect(reader,root/'output',root/'cache',license_file)
                self.assertFalse((root/'output/materials/catalog.json').exists())

    def test_public_downloads_cannot_change_origin(self):
        reader=module.Reader('https://registry.example/api/material-registry/v1')
        with self.assertRaises(ValueError):reader.url('https://other.example/package.zip')


if __name__=='__main__':unittest.main()
