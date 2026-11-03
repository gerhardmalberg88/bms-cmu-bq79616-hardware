"""Verify configured heat loads against the saved PCB and published steady inputs.

Run in an environment with pcb-thermal-lab installed; no solver or native results
are required. This hardware-specific regression belongs beside the case inputs.
"""
import json
import unittest
from pathlib import Path

from pcb_thermal.config import load
from pcb_thermal.extract import sexpr
from pcb_thermal.power import derive

HERE = Path(__file__).resolve().parent
NODE_REFS = ['R361', 'R354', 'R347', 'R340', 'R333', 'R326', 'R319', 'R312',
             'R304', 'R362', 'R355', 'R348', 'R341', 'R334', 'R327', 'R320', 'R313']


def board_components(path):
    """Read only saved reference/value/net assertions, without KiCad GUI or writes."""
    components = []
    for item in sexpr(path.read_text())[1:]:
        if not isinstance(item, list) or item[0] != 'footprint':
            continue
        children = [c for c in item if isinstance(c, list)]
        props = {c[1]: c[2] for c in children if c[0] == 'property'}
        if props.get('Reference') not in NODE_REFS:
            continue
        pads = []
        for pad in (c for c in children if c[0] == 'pad'):
            net = next(c for c in pad if isinstance(c, list) and c[0] == 'net')
            pads.append({'net': net[-1]})
        dnp = any((c[0] == 'attr' and 'dnp' in c) or c == ['dnp', 'yes'] for c in children)
        components.append({'ref': props['Reference'], 'value': props['Value'], 'pads': pads, 'dnp': dnp})
    return {'components': components}


class ConfiguredHeatSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, _, _, board, _ = load(HERE/'config.json')
        cls.board = board_components(board)
        cls.published = json.loads((HERE/'report/provenance.json').read_text())['physical_inputs']

    def test_all_schedules_preserve_published_electrical_and_physical_inputs(self):
        for filename, schedule in [('config', 'automatic'), ('odd', 'odd'), ('even', 'even')]:
            with self.subTest(schedule=schedule):
                _, case, _, _, out = load(HERE/(filename+'.json'))
                self.assertEqual(case['sources']['schedule'], schedule)
                for key, value in self.published['sources'].items():
                    if key != 'schedule':self.assertEqual(case['sources'][key], value)
                for key in ('geometry', 'materials', 'cooling', 'assumptions'):
                    self.assertEqual(case[key], self.published[key])
                self.assertEqual(out.parent.name, 'configured')
                self.assertEqual(out.name, schedule+'-h10')
                self.assertEqual([n['ref'] for n in case['sources']['nodes']], NODE_REFS)
                power = derive(self.board, case)
                self.assertAlmostEqual(power['total_w'], 3.2854850045326165, places=13)
                self.assertAlmostEqual(power['switch_loss_w'], 0.11909883141430735, places=13)
                phase_power = (4.2 / 41.45)**2 * 20
                for i, ref in enumerate(NODE_REFS):
                    resistor = power['resistors'][ref]
                    odd = phase_power if i < 16 else 0.
                    even = phase_power if i > 0 else 0.
                    self.assertAlmostEqual(resistor['odd_w'], odd, places=13)
                    self.assertAlmostEqual(resistor['even_w'], even, places=13)
                    self.assertAlmostEqual(resistor['average_w'], (odd+even)/2 if schedule=='automatic' else {'odd':odd,'even':even}[schedule], places=13)


if __name__ == '__main__':
    unittest.main()
