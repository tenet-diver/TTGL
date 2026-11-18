"""Preserve host checkpoint modes through the owned actor import boundary."""
import os
import json
import subprocess
import time
from pathlib import Path
from ..experience_routing.execution import DockerWorkspace, docker, source_tar
from ..experience_routing.io import digest


class ExactModeActor(DockerWorkspace):
    def _create(self, name):
        # Coding tasks execute their tracked scripts. Docker's implicit tmpfs
        # noexec default prevents prescribed bin/test commands despite0755.
        docker('create', '--name', name, '--network', 'none', '--cap-drop', 'ALL',
               '--security-opt', 'no-new-privileges', '--read-only', '--user', '1000:1000',
               '--pids-limit', '128', '--memory', str(self.memory), '--cpus', str(self.cpus),
               '--tmpfs', '/testbed:rw,exec,nosuid,nodev,size=536870912,uid=1000,gid=1000',
               '--tmpfs', '/tmp:rw,noexec,nosuid,nodev,size=134217728,uid=1000,gid=1000',
               '--env', 'HOME=/tmp/home', '--workdir', '/testbed',
               '--label', 'observatory.experience=true', '--entrypoint', 'sleep', self.image, 'infinity')
        try:
            docker('start', name)
            info = json.loads(docker('inspect', name))[0]
            if info['HostConfig']['NetworkMode'] != 'none' or info['Mounts']:
                raise ValueError('Actor has unexpected network or host mounts')
            return info
        except BaseException:
            docker('rm', '-f', name)
            raise

    def before_attempt(self, workspace):
        archive = source_tar(workspace)
        docker('exec', self.name, 'sh', '-c', 'find /testbed -mindepth 1 -maxdepth 1 -exec rm -rf {} +')
        # BusyBox tar otherwise applies the actor's umask even to original
        # host-owned files. Exporting then falsely attributes mode changes.
        docker('exec', '-i', self.name, 'sh', '-c', 'umask 000; tar -xpf - -C /testbed', input=archive)

    def public_check(self, argv, workspace, timeout, *, raw_output=None):
        name = 'ttgl-worker-'+digest([self.name, 'verify', os.urandom(16).hex()])[:24]
        created = False
        raw = b''
        try:
            self._create(name); created = True
            docker('exec', '-i', name, 'sh', '-c', 'umask 000; tar -xpf - -C /testbed', input=source_tar(workspace))
            started = time.monotonic()
            process = subprocess.run(['docker', 'exec', name, *argv], stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, timeout=timeout)
            duration = time.monotonic()-started
            raw = process.stdout
            result = {'returncode': process.returncode, 'infrastructure_error': False,
                      'command_runtime_seconds': duration, 'pristine_image': self.image,
                      'agent_runtime_changes_excluded': True}
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
            raw = error.stdout or b'' if isinstance(error, subprocess.TimeoutExpired) else str(type(error).__name__).encode()
            result = {'returncode': None, 'infrastructure_error': True}
        finally:
            if created: docker('rm', '-f', name)
        if raw_output is not None:
            path = Path(raw_output)
            with path.open('xb') as stream:
                path.chmod(0o600); stream.write(raw)
        return {**result, 'output': raw.decode(errors='replace')}
