"""Check that the installed CLI forwards workspace options without interpreting them."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

CLI = Path(__file__).resolve().parents[1] / 'scripts/ember'
with tempfile.TemporaryDirectory(prefix='ember-entry-') as scratch:
    root = Path(scratch) / 'product with spaces'
    core = root / 'openember'
    (core / 'scripts/kconfig').mkdir(parents=True)
    (root / 'apps/client').mkdir(parents=True)
    (root / 'CMakeLists.txt').touch()
    (core / 'scripts/kconfig/menuconfig.sh').touch()
    (core / 'scripts/ember').write_text(
        '#!/usr/bin/env bash\n'
        'python3 - "$@" <<\'CHECK\'\n'
        'import json, os, sys\n'
        'print(json.dumps([os.environ["OPENEMBER_ROOT"], sys.argv[1:]]))\n'
        'CHECK\n'
    )
    env = dict(os.environ)
    env.pop('OPENEMBER_ROOT', None)
    for command in ('savedefconfig', 'defconfig', 'menuconfig', 'update', 'build', 'run'):
        args = [command, '--product', 'P05W_C0_HW1D0']
        if command == 'build':
            args += ['-j4']
        result = subprocess.run(['bash', str(CLI), *args], cwd=root / 'apps/client',
                                env=env, capture_output=True, text=True, check=True)
        assert json.loads(result.stdout) == [str(root), args], result
    env['OPENEMBER_ROOT'] = str(root)
    result = subprocess.run(['bash', str(CLI), 'savedefconfig'], cwd=scratch,
                            env=env, capture_output=True, text=True, check=True)
    assert json.loads(result.stdout) == [str(root), ['savedefconfig']]
    # Completion can be loaded before a workspace is selected.
    result = subprocess.run(['bash', '-c',
        'source <(bash "$1" completion bash); '
        'COMP_WORDS=(ember save); COMP_CWORD=1; _ember_complete; '
        '[[ " ${COMPREPLY[*]} " == *" savedefconfig "* ]]', '_', str(CLI)],
        cwd=scratch, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
print('Workspace forwarding and completion checks passed')
