"""Build selective offline collections from a verified public/v1 snapshot.

The original distribution ZIPs remain byte-for-byte intact, including resources
whose local directory names collide. This script does not contact any server.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import zipfile


def encoded(value: object) -> bytes:
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()


def member(archive: zipfile.ZipFile, name: str, payload: bytes) -> None:
    info=zipfile.ZipInfo(name,(1980,1,1,0,0,0))
    info.create_system=3
    info.external_attr=0o100644<<16
    info.compress_type=zipfile.ZIP_STORED
    archive.writestr(info,payload)


def build(public_dir: Path, output: Path, version: str) -> dict[str, object]:
    output.mkdir(parents=True,exist_ok=True)
    license_text=(public_dir/'DATA-LICENSE.md').read_bytes()
    artifacts={}
    for kind,key,id_field in [('materials','materials','material_id'),('luts','items','lut_id')]:
        rows=json.loads((public_dir/kind/'catalog.json').read_text())[key]
        entries=[]; identities=set()
        destination=output/f'lumina-{kind}-seed.zip'
        with zipfile.ZipFile(destination,'w') as archive:
            for row in sorted(rows,key=lambda value:(value[id_field],value['revision_id'])):
                identity=(row[id_field],row['revision_id'])
                if identity in identities or row['channel'] not in {'official','community'}:
                    raise ValueError('Only unique approved public revisions belong in the collection')
                identities.add(identity)
                relative=PurePosixPath(row['package_url'])
                if relative.is_absolute() or '..' in relative.parts or '\\' in str(relative):
                    raise ValueError('The snapshot must contain local distribution package paths')
                payload=(public_dir/relative).read_bytes()
                digest=hashlib.sha256(payload).hexdigest()
                if digest!=str(row['package_sha256']).removeprefix('sha256:') or len(payload)!=row['package_bytes']:
                    raise ValueError('A public distribution package failed its checksum')
                manifest_name='lumina_material_bundle.json' if kind=='materials' else 'lumina_lut_bundle.json'
                with zipfile.ZipFile(io.BytesIO(payload)) as original:
                    manifest=json.loads(original.read(manifest_name))
                    original_package=manifest['packages'][0] if kind=='materials' else manifest
                for field in (id_field,'revision_id','content_hash','channel'):
                    if row[field]!=original_package[field]:raise ValueError('Snapshot identity differs from its package')
                path=f'packages/{digest}.zip'
                member(archive,path,payload)
                entries.append({**original_package,'display':row.get('display',original_package.get('display',{})),
                    'path':path,'package_sha256':digest,'package_bytes':len(payload)})
            name='lumina_material_seed.json' if kind=='materials' else 'lumina_lut_seed.json'
            member(archive,name,encoded({'kind':'lumina_material_seed' if kind=='materials' else 'lumina_lut_seed',
                'schema_version':'1.0','dataset_version':version,'packages':entries}))
            member(archive,'DATA-LICENSE.md',license_text)
        artifacts[kind]={'path':destination.name,'bytes':destination.stat().st_size,
            'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'manifest':name,
            'material_count' if kind=='materials' else 'lut_count':len(entries),
            'download_url':f'https://github.com/lumina-layer-studio/Lumina-materials/releases/download/v{version}/{destination.name}'}
    release={'kind':'lumina_resource_release','schema_version':1,'dataset_version':version,'artifacts':artifacts,
        'selection':{'basis':'all_current_approved_public_resources','publication_review':True,'calibration_review':False},
        'licenses':{'new_contributions':'LicenseRef-Lumina-Data-1.0 with explicit contributor consent',
            'existing_data':'Original per-resource licenses and source information are retained; no retroactive relicensing'}}
    (output/'resource-release.json').write_bytes(json.dumps(release,ensure_ascii=False,sort_keys=True,indent=2).encode()+b'\n')
    return release


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--public-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--dataset-version',required=True)
    args=parser.parse_args()
    result=build(args.public_dir,args.output,args.dataset_version)
    print(json.dumps({'dataset_version':result['dataset_version'],'artifacts':result['artifacts']},ensure_ascii=False,indent=2))
