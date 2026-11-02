#!/usr/bin/env python3
"""Single cell-filter study entrypoint. SPDX-License-Identifier: CERN-OHL-P-2.0"""
import signal
from wired_study import main

if __name__=='__main__':
    signal.signal(signal.SIGTERM,lambda *_: (_ for _ in ()).throw(SystemExit(143)))
    main()
