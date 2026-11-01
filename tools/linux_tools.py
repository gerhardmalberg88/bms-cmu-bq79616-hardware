"""Linux executable discovery and isolated FreeCAD readback runtime."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess


def executable(value, default):
    requested = str(value or default)
    found = shutil.which(requested)
    if not found:
        raise SystemExit(f'Required executable not found or not executable: {requested}. Install it or supply an explicit path.')
    return str(Path(found).resolve())


def add_tool_arguments(parser):
    parser.add_argument('--kicad-cli', help='KiCad CLI executable (default: kicad-cli on PATH)')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--freecad-python', help='Explicit Python interpreter with compatible FreeCAD bindings')
    group.add_argument('--freecad-appimage', type=Path, help='Linux FreeCAD AppImage; extracted into ignored build cache')


def freecad_command(args, cache):
    if args.freecad_python:
        return [executable(args.freecad_python, 'python3')], True
    if args.freecad_appimage:
        app = args.freecad_appimage.expanduser().resolve()
        if not app.is_file():
            raise SystemExit(f'FreeCAD AppImage does not exist: {app}')
        digest = hashlib.sha256(app.read_bytes()).hexdigest()
        target = cache / 'freecad' / digest
        launcher = target / 'squashfs-root/AppRun'
        marker = target / 'extracted'
        if not marker.exists():
            target.mkdir(parents=True, exist_ok=True)
            with (target / 'extraction.log').open('w') as log:
                subprocess.run([str(app), '--appimage-extract'], cwd=target, stdout=log, stderr=subprocess.STDOUT, check=True)
            if not launcher.is_file():
                raise SystemExit('FreeCAD AppImage extraction did not produce AppRun')
            marker.write_text(digest + '\n')
        return [str(launcher), 'freecadcmd'], False
    return [executable(None, 'freecadcmd')], False


def run_freecad(args, cache, code, output, log):
    command, _ = freecad_command(args, cache.parent / "tool-cache")
    script = cache / 'step-readback.py'
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(code.replace('Path(sys.argv[1])', "Path(os.environ['CMU_READBACK_OUTPUT'])").replace('import json,sys', 'import json,sys,os'), encoding='utf-8')
    home = cache / 'freecad-home'
    (home / '.config').mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, CMU_READBACK_OUTPUT=str(output), QT_QPA_PLATFORM='offscreen',
               HOME=str(home), XDG_CONFIG_HOME=str(home / '.config'))
    with log.open('w') as handle:
        subprocess.run(command + [str(script)], env=env, stdout=handle, stderr=subprocess.STDOUT, check=True)
