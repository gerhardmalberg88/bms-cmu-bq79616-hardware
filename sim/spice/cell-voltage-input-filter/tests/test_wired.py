"""Checks of the actual approved schematic, case controls and strict result handling."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import wired_study as w


class WiredTests(unittest.TestCase):
    def test_exact_drawing_export_connectivity(self):
        spec=importlib.util.spec_from_file_location('prepare_wired',w.CASE/'prepare-wired-review.py')
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);mod.generate(p/w.SCH.name,p/'audit')
            self.assertEqual((p/w.SCH.name).read_bytes(),w.SCH.read_bytes())
            layout=json.loads((p/'audit/layout.json').read_text())
        base,_=w.load()
        parent={}
        def find(p):
            p=tuple(p);parent.setdefault(p,p)
            if parent[p]!=p:parent[p]=find(parent[p])
            return parent[p]
        def union(a,b):parent[find(a)]=find(b)
        for a,b in layout['wires']:union(a,b)
        observed_to_drawn={};drawn_to_observed={}
        for name,part in layout['parts'].items():
            terms=part['terminals']
            if part['kind']=='GND':actual=['0']
            else:
                f=base[name]
                actual=f[1:5] if part['kind']=='Relais' else f[1:3]
                if part['kind']=='Relais':terms=[terms[i] for i in [1,2,0,3]]
                elif part.get('vertical') and part['kind'] not in ('Vdc','Idc'):terms=list(reversed(terms))
            for point,node in zip(terms,actual):
                drawn=find(point)
                self.assertEqual(observed_to_drawn.setdefault(node,drawn),drawn,(name,'short'))
                self.assertEqual(drawn_to_observed.setdefault(drawn,node),node,(name,'open'))

    def test_schedule_and_no_overlap(self):
        import re
        normal,fine=w.cases()
        self.assertEqual(fine['max_step'],normal['max_step']/2)
        self.assertEqual({k:v for k,v in normal.items() if k not in ('id','max_step')},
                         {k:v for k,v in fine.items() if k not in ('id','max_step')})
        edges,windows,end=w.schedule(normal)
        self.assertEqual(len(windows),6)
        controls=[]
        for n in range(1,17):
            points=np.array([float(v) for v in re.search(r'PWL\((.*)\)',w.control(normal,n))[1].split()]).reshape(-1,2)
            self.assertTrue(np.all(np.diff(points[:,0])>0))
            controls.append(points)
        t=np.unique(np.r_[np.linspace(0,end,10001),[v for edge in edges for v in edge[:2]]])
        values=np.array([np.interp(t,p[:,0],p[:,1]) for p in controls])
        self.assertFalse(np.any((values[0]>0)&(values[1]>0)))
        for window in windows:
            middle=(window['start_s']+window['end_s'])/2
            self.assertTrue(all(np.interp(middle,p[:,0],p[:,1])==0 for p in controls))
        self.assertEqual([v['phase'] for v in windows],['odd','even']*3)
        self.assertTrue(np.all(values[:,-1]==0))

    def test_time_expression_matches_controls(self):
        import re
        case=w.cases()[0]
        edges,_,end=w.schedule(case)
        t=np.r_[np.linspace(0,end,300),[x for a,b,*_ in edges for x in (a,(a+b)/2,b)]]
        for n in (1,2):
            points=np.array([float(v) for v in re.search(r'PWL\((.*)\)',w.control(case,n))[1].split()]).reshape(-1,2)
            u=np.interp(t,points[:,0],points[:,1])
            for smooth,target in [(False,u),(True,u*u*(3-2*u))]:
                expression=w.control_expression(case,n,smooth).replace('^','**')
                actual=[eval(expression,{'__builtins__':{}},{'time':float(x),'min':min,'max':max}) for x in t]
                np.testing.assert_allclose(actual,target,rtol=0,atol=1e-10)
        base,_=w.load();text,_=w.deck(base,case)
        self.assertIn('Bcommand1 ',text)
        self.assertNotIn('\nV_enable1 ',text)

    def test_only_controls_change(self):
        base,_=w.load();case=w.cases()[0]
        initial=w.configured(base,case);final=w.configured(base,case,True)
        for name,f in base.items():
            if name.startswith('V_enable'):
                self.assertEqual(final[name][3],'DC 0')
                self.assertEqual(initial[name][1:3],f[1:3])
            else:self.assertEqual(initial[name],f)

    def test_settle_uses_last_violation(self):
        t=np.arange(6.)
        self.assertEqual(w.settle(t,np.array([[2],[0],[2],[0],[0],[0]]),1,.5),2.)
        self.assertIsNone(w.settle(t,np.ones((6,1)),1,.5))

    def test_netlist_and_prefix_units(self):
        self.assertEqual(w.number('30M'),.03)
        self.assertEqual(w.number('1meg'),1e6)
        with self.assertRaises(ValueError):w.number('bad')
        base,_=w.load();d,columns=w.deck(base,dict(id='test',analysis='op'))
        self.assertIn('Brelax16',d)
        self.assertNotIn('C_relax16 ',d)
        self.assertEqual(len(columns),152)
        self.assertIn('let cell0 = 0*v(',d)

    def test_changed_sources_and_artifacts_rejected(self):
        with patch.object(w,'digest',return_value='changed'):
            with self.assertRaisesRegex(ValueError,'changed'):w.load()
        with tempfile.TemporaryDirectory() as tmp,patch.object(w,'RAW',Path(tmp)):
            p=Path(tmp)/'test';p.mkdir()
            (p/'status.json').write_text(json.dumps(dict(status='failed')))
            with self.assertRaisesRegex(ValueError,'Incomplete'):w.read(dict(id='test'))

    def test_window_excludes_next_on(self):
        from wired_report import window_results
        case=w.cases()[0];windows=w.schedule(case)[1]
        times=sorted({0.,case['duration']}|{x for v in windows for x in [v['start_s'],v['start_s']+.001,v['end_s']-1e-6,v['end_s']]})
        data=np.zeros((len(times),153));data[:,0]=times
        for v in windows:
            data[np.isclose(data[:,0],v['end_s'],rtol=0,atol=1e-12),1]=1.
        rows,_=window_results(data,np.zeros((1,153)),case)
        self.assertTrue(all(r['VC_settling_ms']==0 for r in rows))

    def test_timeout_cleans_owned_process_group(self):
        import subprocess
        import os
        import time
        original=subprocess.Popen
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);pidfile=path/'child.pid';launched=[]
            code=("import subprocess,time; from pathlib import Path; "
                  "p=subprocess.Popen(['sleep','20']); "
                  f"Path({str(pidfile)!r}).write_text(str(p.pid)); time.sleep(20)")
            def launch(*args,**kw):
                self.assertTrue(kw.get('start_new_session'))
                p=original([sys.executable,'-c',code],**kw)
                launched.append(p)
                return p
            started=time.monotonic()
            with patch.object(w.subprocess,'Popen',side_effect=launch):
                with self.assertRaises(subprocess.TimeoutExpired):
                    w.execute(path,'Test timeout\n.end\n',timeout=.3)
            self.assertLess(time.monotonic()-started,4.)
            self.assertIsNotNone(launched[0].poll())
            self.assertTrue(pidfile.exists())
            stat=Path('/proc')/pidfile.read_text()/'stat'
            if stat.exists():
                self.assertEqual(stat.read_text().split()[2],'Z')

    def test_failed_solver_and_truncated_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            with self.assertRaises(RuntimeError):
                w.execute(p,'Broken circuit\nthis_is_invalid\n.end\n')
            good='''Short output
V1 p 0 1
R1 p 0 100
.control
set wr_singlescale
set wr_vecnames
tran 1u 10u
wrdata response.dat v(p)
quit
.endc
.end
'''
            with self.assertRaisesRegex(ValueError,'Truncated'):w.execute(p,good,duration=.1)


if __name__=='__main__':unittest.main()
