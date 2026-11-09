import subprocess
import sys
import textwrap


def test_spawn_with_high_nofile_limit():
    # Isolate the PTY/fork and descriptor cleanup from the test runner. Report
    # a container-sized limit without needing permission to raise the hard limit.
    result = subprocess.run([sys.executable, "-c", textwrap.dedent('''
        import asyncio
        import logging
        import os
        import select
        import signal
        import sys

        from webtiles import terminal

        asyncio.set_event_loop(asyncio.new_event_loop())
        terminal.resource.getrlimit = lambda which: (1073741816, 1073741816)

        # These must be closed explicitly: exec will retain inheritable fds.
        inherited = os.open(os.devnull, os.O_RDONLY)
        os.set_inheritable(inherited, True)
        os.dup2(inherited, 128, inheritable=True)
        program = """
        import errno
        import os
        import sys
        for fd in map(int, sys.argv[1:]):
            try:
                os.fstat(fd)
            except OSError as error:
                assert error.errno == errno.EBADF
            else:
                raise AssertionError('inherited fd was not closed')
        assert os.isatty(0) and os.isatty(1)
        assert os.environ['COLUMNS'] == '80' and os.environ['LINES'] == '24'
        os.write(1, b'pty-ok\\\\n')
        os.write(2, b'stderr-ok\\\\n')
        """
        recorder = terminal.TerminalRecorder(
            [sys.executable, '-c', program, str(inherited), '128'],
            logging.getLogger('test'), (80, 24), {}, None)
        recorder._spawn()
        try:
            # The old billion-close loop times out here. Always kill/reap the
            # child on failure so regression runs cannot leave a CPU spinner.
            ready, _, _ = select.select([recorder.errpipe_read], [], [], 5)
            assert ready, 'spawn stalled before exec'
            assert os.read(recorder.errpipe_read, 4096) == b'stderr-ok\\n'
            assert os.read(recorder.child_fd, 4096) == b'pty-ok\\r\\n'
        finally:
            try:
                os.kill(recorder.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            os.waitpid(recorder.pid, 0)
    ''')], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
