"""Real-image regression: actor commands can use runtimes supplied by the image."""
import asyncio
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from ttgl.harbor_bridge import EnvironmentBridge


@pytest.mark.skipif(not os.environ.get('TTGL_RUNTIME_PATH_IMAGE'),
                    reason='Requires an already-local pinned Linux image with Go on its configured PATH')
def test_actor_can_execute_the_image_go_toolchain(tmp_path):
    image = os.environ['TTGL_RUNTIME_PATH_IMAGE']

    class LocalContainer:
        async def exec(self, *, command, timeout_sec):
            # Same non-login outer shell as Harbor's DockerUnix exec adapter.
            process = await asyncio.create_subprocess_exec(
                'docker', 'run', '--rm', '--pull=never', '--network', 'none',
                '--read-only', '--entrypoint', 'bash', image, '-c', command,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_sec+15)
            return SimpleNamespace(return_code=process.returncode,
                                   stdout=stdout.decode(), stderr=stderr.decode())

    async def scenario():
        bridge = EnvironmentBridge(LocalContainer(), '/app', tmp_path/'trace.jsonl')
        result = await bridge.execute('command -v go && GOTOOLCHAIN=local go version', 15)
        assert result['exit_code'] == 0, result
        assert '/usr/local/go/bin/go' in result['stdout']
        assert 'go version go' in result['stdout']

    asyncio.run(scenario())
