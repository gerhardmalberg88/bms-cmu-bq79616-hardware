#!/usr/bin/env python3
"""Verify the current Qucs-S native export against the approved wired drawing.

SPDX-License-Identifier: CERN-OHL-P-2.0
"""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from wired_study import export
from test_wired import WiredTests

if __name__=='__main__':
    export()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([
        WiredTests('test_exact_drawing_export_connectivity')]))
    raise SystemExit(not result.wasSuccessful())
