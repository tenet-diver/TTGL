#!/usr/bin/env python3
"""Data-only text import derivative of the already pinned FastEmbed runtime.

No package execution, install, downloads or model calls. Pillow and image
entry points are excluded. Text tokenization and inference bodies stay exact.
The original runtime remains untouched and available as historical evidence.
"""
import argparse
import ast
from datetime import datetime,timezone
import difflib
import hashlib
import json
from pathlib import Path
import shutil


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(original,target,receipt,patch):
    target.mkdir(parents=True,exist_ok=False)
    source=original/'memory-runtime';runtime=target/'memory-runtime';runtime.mkdir()
    excluded=[]
    for path in source.iterdir():
        if path.name=='PIL' or path.name.startswith(('pillow.libs','pillow-')):
            excluded.append(path.name);continue
        if path.name in ('fastembed','fastembed-0.9.1.dist-info'):
            shutil.copytree(path,runtime/path.name,ignore=shutil.ignore_patterns('__pycache__'))
        else:(runtime/path.name).symlink_to(path.resolve(),target_is_directory=path.is_dir())
    if not excluded:raise ValueError('Expected explicit Pillow exclusions')
    edits={
        'fastembed/__init__.py':[
            ('from fastembed.image import ImageEmbedding\n',''),
            ('from fastembed.late_interaction import LateInteractionTextEmbedding\n',''),
            ('from fastembed.late_interaction_multimodal import LateInteractionMultimodalEmbedding\n',''),
            ('    "ImageEmbedding",\n',''),('    "LateInteractionTextEmbedding",\n',''),
            ('    "LateInteractionMultimodalEmbedding",\n','')],
        'fastembed/common/types.py':[('from PIL import Image\n',''),('ImageInput: TypeAlias = PathInput | Image.Image','ImageInput: TypeAlias = PathInput')],
        'fastembed/common/preprocessor_utils.py':[
            ('from fastembed.image.transform.operators import Compose\n',''),
            ('def load_preprocessor(model_dir: Path) -> Compose:',
             'def load_preprocessor(model_dir: Path) -> Any:\n    raise NotImplementedError("Image preprocessing excluded from TTGL text-only derivative")')],
    }
    differences=[];hashes={}
    for name,replacements in edits.items():
        path=runtime/name;before=path.read_text();after=before
        for old,new in replacements:
            if after.count(old)!=1:raise ValueError('Unexpected upstream import shape: '+name)
            after=after.replace(old,new)
        path.write_text(after);ast.parse(after)
        differences.extend(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),fromfile='a/'+name,tofile='b/'+name))
        hashes[name]=dict(original=digest(source/name),derived=digest(path))
    # Image routes are unavailable, rather than falling back to another codec.
    for name in ('image','late_interaction_multimodal'):
        shutil.rmtree(runtime/'fastembed'/name)
    metadata=runtime/'fastembed-0.9.1.dist-info/METADATA'
    before=metadata.read_text();lines=before.splitlines(keepends=True)
    removed=[x for x in lines if x.lower().startswith('requires-dist: pillow')]
    if len(removed)!=3:raise ValueError('Unexpected Pillow dependency declarations')
    after=''.join(x for x in lines if x not in removed);metadata.write_text(after)
    differences.extend(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),fromfile='a/fastembed-0.9.1.dist-info/METADATA',tofile='b/fastembed-0.9.1.dist-info/METADATA'))
    hashes['fastembed-0.9.1.dist-info/METADATA']=dict(original=digest(source/'fastembed-0.9.1.dist-info/METADATA'),derived=digest(metadata))
    # Assert every text algorithm/tokenizer body remains byte-identical.
    checked=0
    for path in (source/'fastembed/text').rglob('*.py'):
        relative=path.relative_to(source)
        if path.read_bytes()!=(runtime/relative).read_bytes():raise ValueError('Text inference source changed')
        checked+=1
    before_tree=ast.parse((source/'fastembed/common/preprocessor_utils.py').read_text())
    after_tree=ast.parse((runtime/'fastembed/common/preprocessor_utils.py').read_text())
    for node in before_tree.body:
        if isinstance(node,ast.FunctionDef) and node.name!='load_preprocessor':
            derived=next(n for n in after_tree.body if isinstance(n,ast.FunctionDef) and n.name==node.name)
            if ast.dump(node,include_attributes=False)!=ast.dump(derived,include_attributes=False):raise ValueError('Tokenizer behavior changed')
    for name in ('embedding-model','embedding-model-receipt.json','graphiti-runtime'):
        (target/name).symlink_to((original/name).resolve(),target_is_directory=(original/name).is_dir())
    patch.write_text(''.join(differences))
    value=dict(at=datetime.now(timezone.utc).isoformat(),source=str(source.resolve()),target=str(target.resolve()),
        excluded=excluded,excluded_routes=['fastembed/image','fastembed/late_interaction_multimodal'],edits=hashes,
        exact_text_source_files=checked,tokenizer_function_bodies_unchanged=True,patch_sha256=digest(patch),
        package_variant='FastEmbed 0.9.1, explicit TTGL text-only import derivative 001',
        installed_downloads=False,model_calls=0,original_runtime_changed=False,
        limitation='Not stock full FastEmbed. Image APIs unavailable; graph/storage/ranking/text inference unchanged. Requires runtime equivalence check before new scored calls.')
    receipt.write_text(json.dumps(value,indent=2)+'\n');return value


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('original','target','receipt','patch'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();print(json.dumps(prepare(a.original.resolve(),a.target.resolve(),a.receipt,a.patch)))
