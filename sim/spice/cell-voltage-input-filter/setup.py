#!/usr/bin/env python3
"""Install a checksum-verified Qucs-S into the repository's ignored build area.

SPDX-License-Identifier: CERN-OHL-P-2.0
"""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / 'build/cell-voltage-input-filter/tools'
URL = 'https://github.com/ra3xdh/qucs_s/releases/download/26.1.1/Qucs-S-26.1.1-linux-x86_64.AppImage'
SHA256 = 'a86ab951118bfdffc8acfda8893cde0e2aeedc7129cc73978ae7d16761ec5cb5'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--appimage', type=Path, help='Use an already downloaded, matching release')
    args = p.parse_args()
    missing = [x for x in ('ngspice', 'kicad-cli') if not shutil.which(x)]
    if missing:
        p.error('Missing ' + ', '.join(missing) + '. Ubuntu: sudo apt install ngspice kicad')
    try:
        import numpy, scipy, matplotlib, pcbnew  # noqa: F401
    except ImportError as e:
        p.error(f'{e}. Run with /usr/bin/python3; Ubuntu packages: python3-numpy python3-scipy python3-matplotlib kicad')
    TOOLS.mkdir(parents=True, exist_ok=True)
    image = args.appimage or TOOLS / 'Qucs-S.AppImage'
    if not image.exists():
        temporary = image.with_suffix('.download')
        with urllib.request.urlopen(URL, timeout=120) as src, temporary.open('wb') as dst:
            shutil.copyfileobj(src, dst)
        if hashlib.sha256(temporary.read_bytes()).hexdigest() != SHA256:
            raise RuntimeError('Downloaded Qucs-S checksum mismatch')
        temporary.replace(image)
    if hashlib.sha256(image.read_bytes()).hexdigest() != SHA256:
        raise RuntimeError('Qucs-S checksum mismatch; release must be 26.1.1')
    if not (TOOLS / 'squashfs-root/AppRun').exists():
        image.chmod(image.stat().st_mode | 0o100)
        subprocess.run([str(image.resolve()), '--appimage-extract'], cwd=TOOLS,
                       stdout=subprocess.DEVNULL, check=True)
    print('Installed Qucs-S 26.1.1:', TOOLS / 'squashfs-root/AppRun')
    print('ngspice:', shutil.which('ngspice'))
    print('Open circuit: /usr/bin/python3 sim/spice/cell-voltage-input-filter/study.py gui')


if __name__ == '__main__':
    main()
