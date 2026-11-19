"""Anonymous physical CLI cwd/home with a private host-side ownership index."""
from pathlib import Path
import tempfile
import json
from ..experience_routing.io import write_new
from ..experience_routing.checkpoints import manifest


def client_paths(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True,mode=0o700)
    physical=Path(tempfile.mkdtemp(prefix='observatory-native-',dir='/tmp'))
    native,workspace=physical/'native',physical/'workspace'
    native.mkdir(mode=0o700);workspace.mkdir(mode=0o700)
    (output/'native').symlink_to(native,target_is_directory=True)
    (output/'client-workspace').symlink_to(workspace,target_is_directory=True)
    write_new(output/'anonymous-client.json',{'native_output':str(native),'workspace':str(workspace),
        'purpose':'Physical CLI cwd/home contain no task, system condition or model identity',
        'authoritative_raw_retention':'Existing loopback S3; local source files remain accessible via private symlinks'})
    return native,workspace


def audit_environment(native,forbidden):
    messages=[];violations=[]
    for file in Path(native).glob('*/client-home/sessions/**/*.jsonl'):
        for line in file.read_text().splitlines():
            row=json.loads(line)
            if row.get('type')!='response_item' or row.get('payload',{}).get('type')!='message':continue
            payload=row['payload']
            if payload.get('role') not in ('user','system','developer'):continue
            for part in payload.get('content',[]):
                text=part.get('text','')
                if '<environment_context>' not in text:continue
                messages.append(text)
                for token in forbidden:
                    if token.casefold() in text.casefold():violations.append(token)
    return {'environment_messages_observed':len(messages),'forbidden_identity_exposed':bool(violations),
            'violations':sorted(set(violations)),
            'scope':'Recorded model-visible environment messages; raw HTTP bodies and pretraining exposure are outside this audit'}


def archive_client_state(native,output,client):
    """Retain the finished private client state before ephemeral storage loss."""
    from .artifacts import _store
    from ..experience_routing.execution import source_tar
    native,output=Path(native),Path(output)
    if list(native.rglob('auth.json')):
        raise ValueError('Client credentials must be removed before state archival')
    before=manifest(native)
    receipt=_store(source_tar(native),output/'native-client-state.tar.gz',client,
                   'closed-native-client-state',before['state_hash'])
    if manifest(native)['state_hash']!=before['state_hash']:
        raise ValueError('Client state changed during capture; preserve local source')
    return {'format':'native-client-tar-gzip-v1','state_hash':before['state_hash'],'archive':receipt}
