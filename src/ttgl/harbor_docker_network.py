"""Narrow Harbor extension for Docker hosts without nftables FIB support.

Use maintained Docker network attachment operations, keeping Harbor's task,
phase, exec, mount and verifier implementations. Only public/no-network phases
on one ordinary Linux container are supported; allowlists are rejected.
"""
import asyncio
import json

from harbor.constants import MAIN_SERVICE_NAME
from harbor.environments.docker.docker import DockerEnvironment
from harbor.models.task.config import NetworkMode


class DetachedNetworkDocker(DockerEnvironment):
    @classmethod
    def _egress_control_kernel_support(cls):
        # This implementation deliberately uses Docker attachments, not nftables.
        return False

    def __init__(self, *args, **kwargs):
        self._detached_networks = None
        self._transition_lock = asyncio.Lock()
        self.network_transitions = []
        super().__init__(*args, **kwargs)
        if self._is_windows_container or self._uses_compose:
            raise ValueError('Detached networking requires one standard Linux task container')

    @property
    def capabilities(self):
        return super().capabilities.model_copy(update={
            'stream': False, 'disable_internet': True,
            'dynamic_network_policy': True, 'docker_compose': False, 'windows': False,
        })

    def validate_network_policy_support(self, network_policy=None):
        policy = network_policy or self.network_policy
        if policy.network_mode not in (NetworkMode.PUBLIC, NetworkMode.NO_NETWORK):
            raise ValueError('Detached networking does not implement allowlists')
        super().validate_network_policy_support(policy)

    async def _docker(self, *args):
        process = await asyncio.create_subprocess_exec(
            *self._engine_cmd(*args), stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), 30)
        except BaseException:
            process.kill()
            await process.wait()
            raise
        if process.returncode:
            raise RuntimeError(f'Docker attachment operation failed: {stderr.decode()}')
        return stdout.decode()

    async def _inspect_actor(self, container):
        rows = json.loads(await self._docker('inspect', container))
        if len(rows) != 1 or not rows[0]['State']['Running']:
            raise RuntimeError('Expected exactly one running actor container')
        row = rows[0]
        host = row['HostConfig']
        if (host.get('Privileged') or host.get('NetworkMode') in ('host', 'none')
                or host.get('PortBindings') or host.get('Devices')
                or {'NET_ADMIN', 'SYS_ADMIN', 'ALL'} & set(host.get('CapAdd') or [])):
            raise RuntimeError('Unsupported actor networking or elevated capabilities')
        for mount in row.get('Mounts', []):
            if mount.get('Destination') in ('/var/run/docker.sock', '/run/docker.sock'):
                raise RuntimeError('Actor must not control the Docker daemon')
        return row

    async def _apply_network_policy(self, network_policy):
        self.validate_network_policy_support(network_policy)
        async with self._transition_lock:
            result = await self._run_docker_compose_command(['ps', '-q', MAIN_SERVICE_NAME])
            containers = result.stdout.strip().splitlines()
            if len(containers) != 1:
                raise RuntimeError('Expected one primary container')
            container = containers[0]
            row = await self._inspect_actor(container)
            networks = row['NetworkSettings']['Networks']
            if network_policy.network_mode == NetworkMode.NO_NETWORK:
                if not networks or self._detached_networks is not None:
                    raise RuntimeError('Unexpected actor attachment state before isolation')
                self._detached_networks = networks
                for name in networks:
                    await self._docker('network', 'disconnect', name, container)
                if (await self._inspect_actor(container))['NetworkSettings']['Networks']:
                    raise RuntimeError('Actor retained network attachments')
            else:
                if networks or not self._detached_networks:
                    raise RuntimeError('Unexpected actor attachment state before restoration')
                for name, metadata in self._detached_networks.items():
                    options = []
                    for alias in metadata.get('Aliases') or []:
                        options += ['--alias', alias]
                    await self._docker('network', 'connect', *options, name, container)
                restored = (await self._inspect_actor(container))['NetworkSettings']['Networks']
                if set(restored) != set(self._detached_networks):
                    raise RuntimeError('Actor attachment restoration did not match setup')
                self._detached_networks = None
            self.network_transitions.append({'container': container,
                                             'mode': network_policy.network_mode.value})
