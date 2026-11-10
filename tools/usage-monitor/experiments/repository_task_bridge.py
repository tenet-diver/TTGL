"""Audited task bridge with the source package's reviewed console scripts on PATH."""
import task_terminal_mcp_v2 as previous


class RepositoryBridge(previous.TaskBridge):
    def execute(self, ident, command, timeout):
        return super().execute(ident, 'export PATH=/task-bin:/usr/local/bin:/usr/bin:/bin\n' + command, timeout)


if __name__ == '__main__':
    previous.TaskBridge = RepositoryBridge
    previous.main()
