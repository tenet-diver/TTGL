"""Native permission-profile controls for each freshly assigned repair workspace."""
import json
from pathlib import Path
import shutil
import subprocess
import sys


def permission_settings(work):
    return {
        'default_permissions':'ttgl_verify',
        'permissions.ttgl_verify.filesystem':{
            ':root':'deny', ':minimal':'read', str(work.resolve()):'write',
            str(Path(sys.prefix).resolve()):'read',
            str(Path(shutil.which('codex')).resolve()):'read'},
        'permissions.ttgl_verify.network.enabled':False,
    }


def check(work, outside, output):
    output.mkdir(parents=True, exist_ok=False)
    command=['codex','sandbox','-P','ttgl_verify','-C',str(work.resolve()),'--include-managed-config']
    for key,value in permission_settings(work).items():
        encoded='{'+','.join(json.dumps(k)+'='+json.dumps(v) for k,v in value.items())+'}' if isinstance(value,dict) else json.dumps(value)
        command+=['-c',key+'='+encoded]
    rows=[]
    for kind,code in [
        ('write','from pathlib import Path; p=Path(".owned-permission-check");p.write_text("inside-ok");print(p.read_text());p.unlink()'),
        ('outside','from pathlib import Path;print(Path('+repr(str(outside.resolve()))+').read_text())')]:
        result=subprocess.run(command+['--',str(Path(sys.executable).resolve()),'-I','-S','-c',code],capture_output=True,text=True,timeout=25)
        (output/(kind+'-stdout.log')).write_text(result.stdout)
        (output/(kind+'-stderr.log')).write_text(result.stderr)
        rows.append(dict(kind=kind,exit_code=result.returncode,
                         inside_exact=result.stdout=='inside-ok\n' if kind=='write' else None,
                         outside_leaked=outside.read_text() in result.stdout,
                         intended_outside_denial=(str(outside.resolve()) in result.stderr and any(t in result.stderr.lower() for t in ('permission denied','no such file','operation not permitted'))) if kind=='outside' else None))
    passed=rows[0]['exit_code']==0 and rows[0]['inside_exact'] and rows[1]['exit_code']!=0 and not rows[1]['outside_leaked'] and rows[1]['intended_outside_denial']
    receipt=dict(passed=passed,work=str(work.resolve()),settings=permission_settings(work),cells=rows,model_calls=0)
    (output/'results.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt
