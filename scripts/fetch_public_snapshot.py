"""Fetch only anonymous approved resources; reuse verified unchanged packages."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode,urljoin,urlsplit
from urllib.request import HTTPRedirectHandler,Request,build_opener

MAX_DOCUMENT=8*1024*1024
MAX_PACKAGE=32*1024*1024


def encoded(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


class Reader:
    def __init__(self,base):
        self.base=base.rstrip('/')+'/'
        origin=urlsplit(self.base)
        if origin.scheme!='https' and not (origin.scheme=='http' and origin.hostname in {'127.0.0.1','localhost'}):
            raise ValueError('Use HTTPS for the public Registry')
        self.origin=(origin.scheme,origin.netloc)
        owner=self
        class SameOrigin(HTTPRedirectHandler):
            def redirect_request(self,request,fp,code,msg,headers,newurl):
                owner.url(newurl)
                return super().redirect_request(request,fp,code,msg,headers,newurl)
        self.opener=build_opener(SameOrigin())

    def url(self,path):
        value=urljoin(self.base,path);parsed=urlsplit(value)
        if (parsed.scheme,parsed.netloc)!=self.origin or parsed.username or parsed.password:
            raise ValueError('Public package changed origin')
        return value

    def bytes(self,path,maximum):
        with self.opener.open(Request(self.url(path),headers={'Accept-Encoding':'identity'}),timeout=45) as response:
            value=response.read(maximum+1)
        if len(value)>maximum:raise ValueError('Public resource exceeds the download limit')
        return value

    def json(self,path,params=()):
        return json.loads(self.bytes(path+('?' + urlencode(params) if params else ''),MAX_DOCUMENT))


def collect(reader,output,cache,license_file):
    if output.exists() and any(output.iterdir()):raise ValueError('Build into an empty staging directory')
    output.mkdir(parents=True,exist_ok=True)
    generated=datetime.now(timezone.utc).isoformat()
    report={'downloaded_package_bytes':0,'reused_packages':0}
    documents={}
    def save(relative,payload):
        path=output/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(payload)
    for kind,key,id_field in [('materials','materials','material_id'),('luts','items','lut_id')]:
        rows=[];total=None;identities=set()
        while total is None or len(rows)<total:
            page=reader.json(kind+'/catalog',[('channel','official'),('channel','community'),('limit','500'),('offset',str(len(rows)))])
            expected=page['total_count']
            if type(expected)is not int or not 0<=expected<=10000 or total is not None and total!=expected:
                raise ValueError('The public catalog changed during pagination')
            total=expected
            batch=page[key]
            if not isinstance(batch,list) or (not batch and len(rows)<total):raise ValueError('Incomplete catalog page')
            for row in batch:
                identity=(row[id_field],row['revision_id'])
                if row['channel'] not in {'official','community'} or identity in identities:
                    raise ValueError('Only unique approved public resources may be published')
                identities.add(identity)
            rows.extend(batch)
            if len(rows)>total:raise ValueError('Catalog pagination exceeded its declared count')
        previous={}
        try:
            old=json.loads((cache/kind/'catalog.json').read_bytes())
            previous={(row[id_field],row['revision_id'],row['content_hash']):row for row in old[key]}
        except (OSError,ValueError,KeyError,TypeError):pass
        for row in rows:
            sha=str(row['package_sha256']).removeprefix('sha256:')
            if len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha):raise ValueError('Invalid public package checksum')
            relative=('' if kind=='materials' else 'luts/')+'packages/'+sha+'.zip'
            path=cache/relative
            payload=path.read_bytes() if path.is_file() else b''
            if len(payload)==row['package_bytes'] and digest(payload)==sha:
                report['reused_packages']+=1
            else:
                payload=reader.bytes(row['package_url'],MAX_PACKAGE)
                report['downloaded_package_bytes']+=len(payload)
            if len(payload)!=row['package_bytes'] or digest(payload)!=sha:raise ValueError('Public package checksum mismatch')
            save(relative,payload);row['package_url']=relative
        if kind=='luts':
            needed=[]
            for row in rows:
                old=previous.get((row[id_field],row['revision_id'],row['content_hash']),{})
                sha=old.get('preview_sha256','')
                path=cache/'luts/previews'/f'{sha}.json'
                if len(sha)==64 and path.is_file() and digest(path.read_bytes())==sha:
                    save('luts/previews/'+sha+'.json',path.read_bytes());row['preview_sha256']=sha
                else:needed.append(row)
            for start in range(0,len(needed),24):
                batch=needed[start:start+24]
                response=reader.json('luts/catalog',[('channel','official'),('channel','community'),('limit','1'),
                    *[('preview_id',row[id_field]) for row in batch]])
                lookup={(p[id_field],p['revision_id'],p['content_hash']):p for p in response.get('previews',[])}
                for row in batch:
                    preview=lookup.get((row[id_field],row['revision_id'],row['content_hash']))
                    if preview:
                        payload=encoded({'schema_version':1,**preview});sha=digest(payload)
                        save('luts/previews/'+sha+'.json',payload);row['preview_sha256']=sha
        stats=[]
        ids=list(dict.fromkeys(row[id_field] for row in rows))
        for start in range(0,len(ids),100):
            batch=ids[start:start+100]
            response=reader.json('resources/'+kind+'/activity',[('resource_id',value) for value in batch])
            for item in response['items']:
                if item['resource_id'] not in batch:raise ValueError('Unexpected public activity identity')
                stats.append({name:item[name] for name in ('resource_id','likes','saves','downloads','revisions')})
        documents[kind+'/catalog.json']={'schema_version':1,'generated_at':generated,key:rows}
        documents[kind+'/activity.json']={'schema_version':1,'generated_at':generated,'items':stats}
        report[kind]=len(rows)
    for relative,document in documents.items():
        payload=encoded(document)
        if len(payload)>MAX_DOCUMENT:raise ValueError('Public metadata exceeds the static client limit')
        try:
            old_bytes=(cache/relative).read_bytes();old=json.loads(old_bytes);new=dict(document)
            old.pop('generated_at',None);new.pop('generated_at',None)
            if old==new:payload=old_bytes
        except (OSError,ValueError,AttributeError):pass
        save(relative,payload)
    save('DATA-LICENSE.md',license_file.read_bytes())
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--cache',type=Path,default=Path('public/v1'))
    parser.add_argument('--license-file',type=Path,default=Path('DATA-LICENSE.md'))
    args=parser.parse_args()
    print(json.dumps(collect(Reader(args.registry),args.output,args.cache,args.license_file)))
