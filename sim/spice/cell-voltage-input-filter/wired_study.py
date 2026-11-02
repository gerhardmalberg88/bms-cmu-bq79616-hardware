#!/usr/bin/env python3
"""Run the approved physically wired Qucs-S model, without redrawing it.

SPDX-License-Identifier: CERN-OHL-P-2.0
"""
import argparse
from copy import deepcopy
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import signal
import shutil
import subprocess
import time

import numpy as np

CASE = Path(__file__).resolve().parent
ROOT = CASE.parents[2]
SCH = CASE/'circuit/cell-filter-16-cells-with-wires.sch'
BUILD = ROOT/'build/cell-voltage-input-filter'
RAW = ROOT/'sim/results/cell-voltage-input-filter/repeated-cycle'
EXPORT = CASE/'circuit/wired-export.cir'
META = CASE/'circuit/wired-export.json'


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def number(token):
    m = re.fullmatch(r'([+-]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][+-]?\d+)?)([a-zA-Z]*)', token)
    if not m:
        raise ValueError('Invalid SPICE number: '+token)
    suffix = m[2].lower()
    scale = {'':1, 't':1e12, 'g':1e9, 'meg':1e6, 'k':1e3, 'm':1e-3,
             'u':1e-6, 'n':1e-9, 'p':1e-12, 'f':1e-15}
    return float(m[1])*scale[suffix]


def elements(text):
    result = {}
    for line in text.splitlines():
        if not line or line[0] in '*.' or line.startswith('#'):
            continue
        f = line.split()
        if f[0][0].upper() not in 'RLCVIS':
            raise ValueError('Unsupported exported device: '+line)
        if f[0] in result:
            raise ValueError('Duplicate component: '+f[0])
        result[f[0]] = f
    return result


def qucs():
    local = BUILD/'tools/squashfs-root/AppRun'
    found = str(local) if local.exists() else shutil.which('qucs-s')
    if not found:
        raise RuntimeError('Install Qucs-S using setup.py')
    return found


def export():
    """Qucs is the connectivity authority; no hand-reconstructed parallel circuit."""
    out = BUILD/'wired-study'; out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, XDG_CONFIG_HOME=str(BUILD/'qucs-profile'))
    command = [qucs(), '-n', '--ngspice', '-i', str(SCH), '-o', str(out/'export.cir')]
    if not os.environ.get('DISPLAY'):
        command = ['xvfb-run', '-a', *command]
    with (out/'export.log').open('w') as log:
        subprocess.run(command, env=env, stdout=log, stderr=log, check=True, timeout=45)
    raw = (out/'export.cir').read_text()
    # Only primitive R/L/C/V/I/S devices: generated global includes are unused.
    # Remove Qucs's no-analysis control block and absolute installation paths.
    lines = raw.split('.control', 1)[0].splitlines()
    clean = '* Native Qucs-S export of cell-filter-16-cells-with-wires.sch\n'
    clean += '\n'.join(l.rstrip() for l in lines if l and not l.startswith('*')
                       and not l.upper().startswith('.INCLUDE'))+'\n'
    devices = elements(clean)
    drawn = [shlex.split(l[1:-1]) for l in SCH.read_text().split('<Components>')[1].split('</Components>')[0].splitlines() if l]
    expected = {f[1]:f for f in drawn if f[0]!='GND'}
    if set(devices)!=set(expected):
        raise ValueError('Qucs export component inventory mismatch')
    for name, f in expected.items():
        d = devices[name]
        if f[0] in ('R','L','C','Vdc','Idc'):
            v = f[9].replace(' ', '').replace('Ohm','').replace('F','').replace('H','').replace('V','').replace('A','')
            # Qucs M = mega, SPICE M = milli.
            v = v.replace('M','meg')
            actual = number(d[4] if f[0] in ('Vdc','Idc') else d[3])
            if not np.isclose(actual, number(v), rtol=1e-10, atol=1e-25):
                raise ValueError('Qucs export value mismatch: '+name)
    EXPORT.write_text(clean)
    write_json(META, dict(schematic_sha256=digest(SCH), export_sha256=digest(EXPORT),
                         components=len(devices), source='Qucs-S native ngspice exporter',
                         removed='unused global library includes; empty control block; local paths',
                         source_hashes=json.loads((CASE/'topology.json').read_text())['source_hashes']))
    print('Exported', len(devices), 'devices from approved schematic')


def load():
    meta = json.loads(META.read_text())
    if meta['schematic_sha256']!=digest(SCH) or meta['export_sha256']!=digest(EXPORT):
        raise ValueError('Schematic/export changed: export and verify again before running')
    for path, h in meta['source_hashes'].items():
        if digest(ROOT/path)!=h:
            raise ValueError('KiCad design changed: '+path)
    return elements(EXPORT.read_text()), meta


def config():
    value=json.loads((CASE/'case.json').read_text())
    if value['cycles']<2 or not isinstance(value['cycles'],int):
        raise ValueError('At least two complete cycles required')
    for key in ['on_s','gap_s','edge_s','max_step_s','voltage_tolerance_V','settling_tolerance_s','settling_band_V','cb_tolerance_V']:
        if not np.isfinite(value[key]) or value[key]<=0:raise ValueError('Invalid '+key)
    if value['max_step_s']>value['edge_s']/2:raise ValueError('Resolve the switching edge')
    return value


def schedule(case):
    """Initial odd DC; successive ON plateaus and nonoverlapping OFF gaps."""
    t=0.;windows=[];edges=[]
    for index in range(2*case['cycles']):
        phase='odd' if index%2==0 else 'even'
        if index:
            edges.append((t,t+case['edge'],phase,0.,1.));t+=case['edge']
        t+=case['on_s']
        edges.append((t,t+case['edge'],phase,1.,0.));t+=case['edge']
        windows.append(dict(cycle=index//2+1,phase=phase,start_s=t,end_s=t+case['gap_s']))
        t+=case['gap_s']
    return edges,windows,t


def cases():
    cfg=config()
    base=dict(id='repeated-cycle',analysis='tran',event='cycle',phase='odd',
              cycles=cfg['cycles'],on_s=cfg['on_s'],gap_s=cfg['gap_s'],edge=cfg['edge_s'],
              max_step=cfg['max_step_s'],reltol=1e-6,vntol=1e-8,abstol=1e-10)
    base['duration']=schedule(base)[2]
    fine=dict(base,id='timestep-check',max_step=base['max_step']/2)
    return [base,fine]


def phase_channels(phase):
    if phase=='off': return set()
    if phase=='odd': return set(range(1,17,2))
    if phase=='even': return set(range(2,17,2))
    raise ValueError('Invalid phase: '+phase)


def pwl(points):
    return 'PWL('+' '.join(f'{t:.12g} {v:.12g}' for t,v in points)+')'


def control(case, n, final=False):
    active=n in phase_channels(case.get('phase','off'))
    if final:return 'DC 0'
    if case.get('event')!='cycle':return f'DC {int(active)}'
    points=[(0.,float(active))]
    phase='odd' if n%2 else 'even'
    for start,end,edge_phase,before,after in schedule(case)[0]:
        if edge_phase==phase:points.extend([(start,before),(end,after)])
    return f'DC {int(active)} '+pwl(points)


def configured(base, case, final=False):
    """Only control stimuli change; all approved component values are retained."""
    devices=deepcopy(base)
    for name,f in devices.items():
        if name.startswith('V_enable'):f[3:]=[control(case,int(name[8:]),final)]
    return devices


def node_map(devices):
    result={}
    for n in range(17):
        for prefix,name,idx in [('cell',f'R_wire{n}',1),('vc',f'I_input{n}',1),
                                ('tap',f'L_PCB{n}',2),('cb',f'R_CBloop{n}',1),
                                ('die',f'L_CBpin{n}',2)]:
            result[prefix+str(n)]=devices[name][idx]
    assert result['cell0']=='0'
    assert result['tap0']!=result['cell0']
    assert all(devices[f'I_input{n}'][2]==result['tap0'] for n in range(17))
    return result



def control_expression(case,n,smooth=False):
    phase='odd' if n%2 else 'even'
    terms=['1' if phase=='odd' else '0']
    for start,end,which,before,after in schedule(case)[0]:
        if which!=phase:continue
        x=f'min(max((time-({start:.12g}))/{end-start:.12g},0),1)'
        value=f'({x})^2*(3-2*({x}))' if smooth else x
        terms.append(f'+({after-before:g})*({value})')
    return '('+''.join(terms)+')'


def switch_gain(f, case):
    if case.get('event')=='cycle':
        # Algebraically identical command; avoids floating-control subtraction.
        return '(1e-10+(0.4-1e-10)*'+control_expression(case,int(f[0][6:]),True)+')'
    u=f'min(max(v({f[3]},{f[4]}),0),1)'
    return f'(1e-10+(0.4-1e-10)*({u})^2*(3-2*({u})))'


def absolute_deck(base, case, final=False):
    if final:case=dict(case,event=None,phase="off")
    d=configured(base,case,final);nodes=node_map(d)
    lines=['Approved wired 16S LG M50 circuit - native Qucs topology']
    for name,f in d.items():
        if name.startswith('V_enable') and case.get('event')=='cycle':
            # Equivalent continuous-time PWL expression without forced breakpoint
            # resets, which can collapse ngspice timesteps in this stiff network.
            lines.append(f'Bcommand{name[8:]} {f[1]} {f[2]} V={control_expression(case,int(name[8:]))}')
            continue
        elif name.startswith('C_relax') and not case.get('native_relax'):
            continue
        if name.startswith('R_relax') and not case.get('native_relax'):
            n=name[7:]; resistance=number(f[3]); capacitance=number(d['C_relax'+n][3])
            # Exact two-terminal R||C impedance, expressed as a ground-referenced
            # state to avoid subtracting large stack voltages across 1 F.
            lines.extend([
                f'Brelax{n} {f[1]} relax_mid{n} V=V(relax_state{n})',
                f'Vsense{n} relax_mid{n} {f[2]} 0',
                f'Bdecay{n} relax_state{n} 0 I=V(relax_state{n})/1000',
                f'Cstate{n} relax_state{n} 0 {resistance*capacitance/1000:.12g}',
                f'Bstate{n} 0 relax_state{n} I=I(Vsense{n})*{resistance/1000:.12g}'])
        elif name.startswith('S_cell'):
            # Same two-terminal conductive path and same control terminals.
            # Smoothstep conductance interpolation, not a claimed TI transistor model.
            ron=case.get('ron',2.5);roff=1e10
            lines.append(f'B{name} {f[1]} {f[2]} I=V({f[1]},{f[2]})*{switch_gain(f,case)}')
        else:lines.append(' '.join(f))
    lines += [f".options reltol={case.get('reltol',1e-4)} vntol={case.get('vntol',1e-6)} abstol={case.get('abstol',1e-8)} method={case.get('method','gear')} maxord=2",
              '.temp 25', '.control','set noaskquit','set wr_singlescale','set wr_vecnames','set numdgt=17']
    analysis='op' if final else case['analysis']
    if analysis=='op':lines+=['op']
    else:
        step=case.get('max_step',1e-5);duration=case.get('duration',.06)
        lines += [f'tran {step:.12g} {duration:.12g} 0 {step:.12g}']
    columns=[]
    for prefix in ['vc','cell','tap','cb','die']:
        for n in range(17):
            key=f'{prefix}{n}'
            expression=f'v({nodes[key]})' if nodes[key]!='0' else f'0*v({nodes["cell1"]})'
            lines.append(f'let {key} = {expression}')
            columns.append(key)
    for n in range(1,17):
        lines.append(f"let cellcurrent{n} = -i(v_cell{n})")
        columns.append(f'cellcurrent{n}')
        f=d[f'S_cell{n}']
        lines.append(f"let balancecurrent{n} = v({f[1]},{f[2]})*{switch_gain(f,case)}")
        columns.append(f'balancecurrent{n}')
    topology=json.loads((CASE/'topology.json').read_text())
    for row in topology['taps']:
        for key in ['vc_cap','cb_cap']:
            ref=row[key]
            name='current_'+ref
            lines.append(f'let {name} = i(l_{ref.lower()}_esl)')
            columns.append(name)
    lines.append('let returncurrent = -i(l_wire0)')
    columns.append('returncurrent')
    lines += ['wrdata response.dat '+' '.join(columns),'quit','.endc','.end']
    return '\n'.join(lines)+'\n',columns


def deck(base,case,final=False):
    if final or case['analysis']!='tran' or case.get('absolute_coordinates'):
        return absolute_deck(base,case,final)
    from wired_dc import independent_dc
    bias,residual,branch=independent_dc(base,case,True)
    if residual>1e-8:raise ValueError('DC origin failed KCL')
    zero=deepcopy(base)
    for name,f in zero.items():
        if name.startswith('V_cell') or name.startswith('I'):f[3:]=['DC','0']
    text,columns=absolute_deck(zero,case)
    nodes=node_map(base)
    for n in range(1,17):
        f=base[f'S_cell{n}'];dv=bias[f[1]]-bias[f[2]]
        g0=.4 if n%2 else 1e-10
        old=next(l for l in text.splitlines() if l.startswith(f'BS_cell{n} '))
        text=text.replace(old,f'BS_cell{n} {f[1]} {f[2]} I=(V({f[1]},{f[2]})+({dv:.17g}))*{switch_gain(f,case)}-({dv*g0:.17g})')
        old=next(l for l in text.splitlines() if l.startswith(f'let balancecurrent{n} = '))
        text=text.replace(old,f'let balancecurrent{n} = (v({f[1]},{f[2]})+({dv:.17g}))*{switch_gain(f,case)}')
    for name,node in nodes.items():
        old=next(l for l in text.splitlines() if l.startswith(f'let {name} = '))
        text=text.replace(old,old+f'+({bias[node]:.17g})')
    for n in range(1,17):
        old=f'let cellcurrent{n} = -i(v_cell{n})'
        text=text.replace(old,old+f'-({branch[f"V_cell{n}"]:.17g})')
    old='let returncurrent = -i(l_wire0)'
    text=text.replace(old,old+f'-({branch["L_wire0"]:.17g})')
    return text,columns


def identity(case):
    _,meta=load()
    files=['wired_study.py','wired_dc.py','case.json','circuit/wired-review.json','circuit/wired-review-geometry.json',
           'topology.json','circuit/wired-export.cir','circuit/wired-export.json']
    return dict(case=case,schematic_sha256=digest(SCH),source_hashes=meta['source_hashes'],
                implementation_and_inputs={f:digest(CASE/f) for f in files},
                ngspice=subprocess.check_output(['ngspice','--version'],text=True),
                switch_representation='Same ports; prescribed smoothstep conductance equivalent to the PWL controls; time expression avoids floating-control subtraction',
                relaxation_representation='Exact R/(1+sRC) two-terminal impedance, scaled ground-referenced state',
                coordinates='Exact perturbations about initial odd DC; switched bias-current terms retained and physical output offsets restored')


def execute(path, text, duration=None, timeout=600):
    path.mkdir(parents=True,exist_ok=True)
    (path/'response.dat').unlink(missing_ok=True)
    (path/'case.cir').write_text(text)
    with (path/'solver.log').open('w') as log:
        process=subprocess.Popen(['ngspice','-n','-b','case.cir'],cwd=path,stdout=log,stderr=log,start_new_session=True)
        try:
            code=process.wait(timeout=timeout)
        finally:
            if process.poll() is None:
                os.killpg(process.pid,signal.SIGTERM)
                try:process.wait(timeout=3)
                except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
    log=(path/'solver.log').read_text()
    if code or re.search(r'aborted|timestep too small|fatal|^error',log,re.I|re.M):
        raise RuntimeError('ngspice failure: '+str(path/'solver.log'))
    data=np.loadtxt(path/'response.dat',skiprows=1,ndmin=2)
    if not np.isfinite(data).all():raise ValueError('Nonfinite output')
    if duration and data[-1,0]<duration*(1-1e-9):raise ValueError('Truncated transient')
    return data


def read(case):
    out=RAW/case['id'];status=json.loads((out/'status.json').read_text())
    if status['status']!='complete':raise ValueError('Incomplete case: '+case['id'])
    current=hashlib.sha256(json.dumps(identity(case),sort_keys=True).encode()).hexdigest()
    if status['fingerprint']!=current:raise ValueError('Stale case: '+case['id'])
    if not status.get('artifacts'):raise ValueError('Missing artifact manifest')
    for rel,h in status['artifacts'].items():
        if digest(out/rel)!=h:raise ValueError('Changed artifact: '+case['id']+'/'+rel)
    data=np.loadtxt(out/'response.dat',skiprows=1,ndmin=2)
    final=np.loadtxt(out/'final/response.dat',skiprows=1,ndmin=2) if case['analysis']=='tran' else None
    return data,final,status


def run(case, force=False):
    base,_=load();out=RAW/case['id'];out.mkdir(parents=True,exist_ok=True)
    ident=identity(case);fp=hashlib.sha256(json.dumps(ident,sort_keys=True).encode()).hexdigest()
    if not force and (out/'status.json').exists():
        try:
            _,_,status=read(case);return status
        except (ValueError,KeyError,FileNotFoundError):pass
    if shutil.disk_usage(ROOT).free<2*2**30:raise RuntimeError('Need 2 GiB available storage')
    if (out/'status.json').exists():
        previous=json.loads((out/'status.json').read_text())
        if previous.get('status') in ('failed','interrupted'):
            archive=RAW/'failed-attempts'/case['id']/str(time.time_ns())
            archive.mkdir(parents=True,exist_ok=True)
            for name in ['status.json','case.cir','solver.log']:
                if (out/name).exists():shutil.copy2(out/name,archive/name)
    text,columns=deck(base,case)
    write_json(out/'inputs.json',ident)
    write_json(out/'columns.json',['scale']+columns)
    status=dict(id=case['id'],status='running',fingerprint=fp)
    write_json(out/'status.json',status);start=time.monotonic()
    try:
        if case['analysis']=='tran':
            final,_=deck(base,case,True)
            execute(out/'final',final)
        data=execute(out,text,case.get('duration',.06) if case['analysis']=='tran' else None)
        load()
        status.update(status='complete',elapsed_s=time.monotonic()-start,rows=len(data),
                      artifacts={str(p.relative_to(out)):digest(p) for p in out.rglob('*') if p.is_file() and p.name!='status.json'})
    except BaseException as exc:
        status.update(status='failed',elapsed_s=time.monotonic()-start,error=str(exc))
        write_json(out/'status.json',status);raise
    write_json(out/'status.json',status)
    return status


def errors(data):
    return np.diff(data[:,1:18],axis=1)-np.diff(data[:,18:35],axis=1)


def settle(t,error,event,band):
    eligible=np.flatnonzero(t>=event)
    if not len(eligible):return None
    bad=eligible[np.any(np.abs(error[eligible])>band,axis=1)]
    idx=bad[-1]+1 if len(bad) else eligible[0]
    return None if idx>=len(t) else float(t[idx]-event)


def csv_write(path,rows):
    with path.open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(rows)


def main():
    parser=argparse.ArgumentParser(description='One repeated balancing-cycle study using the approved Qucs-S circuit.')
    parser.add_argument('action',choices=['export','run','verify','report','all','gui','doctor'])
    parser.add_argument('--force',action='store_true')
    args=parser.parse_args()
    if args.action=='export':export();return
    if args.action=='doctor':
        print(subprocess.check_output(['ngspice','--version'],text=True));print('Qucs-S:',qucs());load();config();return
    if args.action=='gui':
        subprocess.run([qucs(),str(SCH)],check=True,env=dict(os.environ,XDG_CONFIG_HOME=str(BUILD/'qucs-profile')));return
    if args.action in ('run','all'):
        for c in cases():
            print(c['id'],flush=True)
            status=run(c,args.force)
            print(f"  complete: {status['rows']} rows, {status['elapsed_s']:.1f} s",flush=True)
    from wired_report import verify,publish
    if args.action in ('verify','all'):verify()
    if args.action in ('report','all'):publish()


if __name__=='__main__':main()
