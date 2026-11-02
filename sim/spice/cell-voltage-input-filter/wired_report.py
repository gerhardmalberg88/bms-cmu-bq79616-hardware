"""Verification and one report for the repeated balancing-cycle study.

SPDX-License-Identifier: CERN-OHL-P-2.0
"""
import json
import os
from pathlib import Path
import numpy as np
from wired_study import (CASE, RAW, BUILD, SCH, EXPORT, META, cases, config, schedule,
                        read, load, errors, settle, node_map, digest, write_json,
                        csv_write, deck, execute)
from wired_dc import independent_dc

REPORT=CASE/'report'
VERIFY_FILES=['wired_report.py','wired_dc.py','tests/test_wired.py','prepare-wired-review.py']


def window_results(data,final,case):
    """Measure each quiet interval separately; never include the next ON edge."""
    target=errors(final)[0];rows=[];channels=[]
    for window in schedule(case)[1]:
        mask=(data[:,0]>=window['start_s'])&(data[:,0]<window['end_s'])
        d=data[mask]
        if len(d)<2:raise ValueError('Missing quiet-window samples')
        e=errors(d);q=settle(d[:,0],e-target,window['start_s'],config()['settling_band_V'])
        cb=np.diff(d[:,52:69],axis=1)-np.diff(d[:,18:35],axis=1)
        cb_target=(np.diff(final[:,52:69],axis=1)-np.diff(final[:,18:35],axis=1))[0]
        cbq=settle(d[:,0],cb-cb_target,window['start_s'],config()['settling_band_V'])
        rows.append(dict(cycle=window['cycle'],phase=window['phase'],
                         off_start_ms=window['start_s']*1000,gap_ms=case['gap_s']*1000,
                         VC_settling_ms=None if q is None else q*1000,
                         CB_settling_ms=None if cbq is None else cbq*1000,
                         usable_pin_window_ms=None if q is None else (case['gap_s']-q)*1000,
                         end_absolute_VC_error_mV=float(np.max(abs(e[-1]))*1000),
                         end_dynamic_VC_error_mV=float(np.max(abs(e[-1]-target))*1000),
                         worst_end_channel=int(np.argmax(abs(e[-1])))+1))
        for n in range(16):
            qn=settle(d[:,0],(e[:,n]-target[n])[:,None],window['start_s'],config()['settling_band_V'])
            channels.append(dict(cycle=window['cycle'],phase=window['phase'],channel=n+1,
                                 VC_settling_ms=None if qn is None else qn*1000,
                                 final_DC_offset_mV=float(target[n]*1000),
                                 end_absolute_error_mV=float(e[-1,n]*1000),
                                 end_dynamic_error_mV=float((e[-1,n]-target[n])*1000)))
    return rows,channels


def curve_delta(a,b,func):
    av=func(a);bv=func(b)
    return max(float(np.max(abs(av[:,n]-np.interp(a[:,0],b[:,0],bv[:,n])))) for n in range(av.shape[1]))


def verify():
    import importlib.util
    import unittest
    spec=importlib.util.spec_from_file_location('wired_tests',CASE/'tests/test_wired.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    result=unittest.TestResult();mod.WiredTests('test_exact_drawing_export_connectivity').run(result)
    if not result.wasSuccessful():raise ValueError(str(result.errors+result.failures))
    base,meta=load();normal,fine=cases();a,fa,sa=read(normal);b,fb,sb=read(fine)
    for c,d in [(normal,a),(fine,b)]:
        if not np.isfinite(d).all() or np.any(np.diff(d[:,0])<=0) or d[-1,0]<c['duration']*(1-1e-9):
            raise ValueError('Invalid or truncated waveform')
    checks={};limits={}
    def add(name,value,limit):checks[name]=float(value);limits[name]=limit
    add('VC_waveform_difference_V',curve_delta(a,b,errors),config()['voltage_tolerance_V'])
    add('CB_bank_waveform_difference_V',curve_delta(a,b,lambda x:np.diff(x[:,52:69],axis=1)),config()['cb_tolerance_V'])
    wa,_=window_results(a,fa,normal);wb,_=window_results(b,fb,fine)
    for ra,rb in zip(wa,wb):
        for field in ['VC_settling_ms','CB_settling_ms']:
            if ra[field] is None or rb[field] is None:raise ValueError('Quiet window does not settle: '+str(ra))
            add(f"cycle{ra['cycle']}_{ra['phase']}_{field}_difference_s",abs(ra[field]-rb[field])/1000,config()['settling_tolerance_s'])
    evidence=RAW/'verification';evidence.mkdir(exist_ok=True)
    nodes=node_map(base)
    for phase,d in [('odd',b[:1]),('off',fb)]:
        c=dict(id='reference',analysis='op',phase=phase)
        v,kcl=independent_dc(base,c)
        expected=[v[nodes[p+str(n)]] for p in ['vc','cell','tap','cb','die'] for n in range(17)]
        add(phase+'_independent_DC_V',np.max(abs(d[0,1:86]-expected)),1e-7)
        add(phase+'_DC_KCL_A',kcl,1e-8)
        native=EXPORT.read_text()
        if phase=='odd':
            for n in range(1,17,2):
                old=next(l for l in native.splitlines() if l.startswith(f'V_enable{n} '))
                f=old.split();f[-1]='1';native=native.replace(old,' '.join(f))
        native+='\n.options reltol=1e-7 vntol=1e-10 abstol=1e-12\n.control'+deck(base,c)[0].split('.control',1)[1]
        nd=execute(evidence/phase,native)
        add(phase+'_native_export_DC_V',np.max(abs(nd[0,1:86]-expected)),1e-7)
    # Same initial state and first OFF transition in absolute coordinates.
    # End before the next ON edge where floating-node arithmetic loses precision.
    short=dict(fine,duration=fine['on_s']+fine['edge']+.003,absolute_coordinates=True)
    absolute=execute(evidence/'absolute-coordinate-check',deck(base,short)[0],short['duration'])
    segment=b[b[:,0]<=short['duration']]
    add('coordinate_translation_V',curve_delta(segment,absolute,errors),config()['voltage_tolerance_V'])
    failed={k:dict(value=v,limit=limits[k]) for k,v in checks.items() if v>limits[k]}
    validation=dict(passed=not failed,checks=checks,limits=limits,failed=failed,
                    input_hashes={name:digest(CASE/name) for name in VERIFY_FILES},
                    schematic_sha256=digest(SCH),export=meta,
                    records={c['id']:s for c,s in [(normal,sa),(fine,sb)]},
                    verification_artifacts={str(p.relative_to(evidence)):digest(p) for p in evidence.rglob('*') if p.is_file()},
                    scope='One repeated-cycle study; second waveform is timestep verification. No ADC timing or hardware validation.')
    write_json(RAW/'validation.json',validation)
    print(json.dumps(dict(passed=not failed,checks=checks,failed=failed),indent=2),flush=True)
    if failed:raise ValueError('Verification failed; publication blocked')
    return validation


def publish():
    validation=json.loads((RAW/'validation.json').read_text())
    if not validation['passed'] or validation['schematic_sha256']!=digest(SCH):raise ValueError('Current passing verification required')
    for name,sha in validation['input_hashes'].items():
        if digest(CASE/name)!=sha:raise ValueError('Changed verification input: '+name)
    for name,sha in validation['verification_artifacts'].items():
        if digest(RAW/'verification'/name)!=sha:raise ValueError('Changed verification artifact')
    values=[]
    for case in cases():
        d,f,s=read(case)
        if s!=validation['records'][case['id']]:raise ValueError('Results changed after verification')
        values.append((d,f,s))
    # Present the finer waveform, with the coarser run retained only as evidence.
    c=cases()[1];d,f,status=values[1];rows,channels=window_results(d,f,c)
    REPORT.mkdir(exist_ok=True)
    csv_write(REPORT/'windows.csv',rows);csv_write(REPORT/'channels.csv',channels)
    write_json(REPORT/'validation.json',validation)
    os.environ.setdefault('MPLCONFIGDIR',str(BUILD/'matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(4,1,figsize=(11,11),constrained_layout=True)
    # Plot decimation only: numerical measurements always use all native samples.
    idx=np.unique(np.r_[np.arange(0,len(d),max(1,len(d)//12000)),len(d)-1]);t=d[idx,0]*1000
    balance=d[idx,87:118:2]
    axes[0].plot(t,np.sum(balance[:,::2],axis=1),label='Odd channels')
    axes[0].plot(t,np.sum(balance[:,1::2],axis=1),label='Even channels')
    axes[0].set(ylabel='Summed balancing current (A)',title=f"{c['cycles']} diagnostic cycles: {c['on_s']*1000:g} ms ON, {c['gap_s']*1000:g} ms OFF, {c['edge']*1e6:g} us edges")
    e=errors(d);target=errors(f)[0]
    axes[1].plot(t,np.max(abs(e[idx]),axis=1)*1000,label='Worst of 16 channels')
    axes[1].set(ylabel='Absolute VC error (mV)',yscale='log')
    for window,row in zip(schedule(c)[1],rows):
        m=(d[:,0]>=window['start_s'])&(d[:,0]<window['end_s'])
        axes[2].plot((d[m,0]-window['start_s'])*1000,np.maximum(np.max(abs(e[m]-target),axis=1)*1000,1e-8),label=f"Cycle {row['cycle']} {row['phase']}")
    axes[2].axhline(config()['settling_band_V']*1000,color='black',ls='--')
    axes[2].set(xlabel='Time after OFF edge ends (ms)',ylabel='Dynamic VC error (mV)',yscale='log',ylim=(.001,200),xlim=(0,c['gap_s']*1000))
    cb=np.diff(d[idx,52:69],axis=1)
    axes[3].plot(t,cb.min(axis=1),label='Minimum CB-bank differential')
    axes[3].plot(t,cb.max(axis=1),label='Maximum CB-bank differential')
    axes[3].set(xlabel='Time (ms)',ylabel='CB-bank voltage (V)')
    for ax in axes:
        ax.grid(True,alpha=.25);ax.legend(fontsize=8)
    for ax in [axes[0],axes[1],axes[3]]:
        ax.set_xlabel('Time (ms)')
        for w in schedule(c)[1]:ax.axvspan(w['start_s']*1000,w['end_s']*1000,color='green',alpha=.08)
    fig.savefig(REPORT/'repeated-cycle.png',dpi=150);plt.close(fig)
    table='\n'.join(f"| {r['cycle']} | {r['phase']} | {r['VC_settling_ms']:.3f} | {r['CB_settling_ms']:.3f} | {r['usable_pin_window_ms']:.3f} | {r['end_absolute_VC_error_mV']:.3f} |" for r in rows)
    worst=max(r['VC_settling_ms'] for r in rows)
    text=f'''# Repeated balancing cycle — results

One ngspice transient study of the approved wired LG M50 / BQ79616 circuit,
with a separate half-timestep verification run. All numerical checks passed.
No other SPICE studies are published or retained as native results.

The schedule repeats **odd ON → OFF → even ON → OFF** {c['cycles']} times.
Each ON plateau lasts {c['on_s']*1000:g} ms; OFF gaps last {c['gap_s']*1000:g} ms,
with assumed {c['edge']*1e6:g} us smoothstep switching edges.
The first odd phase starts from its DC operating point. These are diagnostic
short-time timings, not a claimed firmware schedule or steady periodic limit.

| Cycle | Phase just switched OFF | VC settling (ms) | CB settling (ms) | Remaining pin-level window (ms) | End absolute VC error (mV) |
|---|---|---:|---:|---:|---:|
{table}

The worst modeled VC settling time is **{worst:.3f} ms**. All {len(rows)} tested OFF gaps
provide a pin-level quiet window under these assumptions. Settling means all
16 differential VC errors remain within **{config()['settling_band_V']*1000:g} mV of the independently solved final
OFF-state offset** through the remainder of that gap. Times start when the
physical OFF edge ends. The next ON edge is excluded. No first-crossing shortcut
is used. Cell-terminal voltage is the reference, so real cell relaxation is not
counted as sensing error.

Waiting does not remove the modeled **{np.max(abs(target))*1000:.3f} mV** maximum DC offset.
Assumed board/input loading through shared wire, contact and fuse impedances
produces the endpoint-channel offsets. These are model predictions, not measured
board errors. The CB values are external capacitor-bank voltages.

![Repeated balancing cycle, VC recovery and CB-bank voltages](repeated-cycle.png)

## Evidence and limits

- [Window measurements](windows.csv), [all 16 channels](channels.csv).
- [Verification](validation.json): waveform timestep agreement, settling-time
  agreement, independent DC/KCL, native Qucs-export DC agreement drawn-wire connectivity and an absolute-coordinate transient
  cross-check through the first OFF transition. Maximum VC waveform difference:
  **{validation['checks']['VC_waveform_difference_V']*1e6:.3f} uV**.
- [Provenance](provenance.json): exact source, implementation and output hashes.
- Native ngspice decks, logs and waveforms:
  `sim/results/cell-voltage-input-filter/repeated-cycle/` (ignored by Git).
- [Run instructions](../README.md), [approved circuit](../circuit/cell-filter-16-cells-with-wires.sch).

The report uses the finer {c['max_step']*1e6:g} us maximum-step waveform. The
{cases()[0]['max_step']*1e6:g} us run is supporting verification of the same study.
Both use Gear integration and identical physical values. Display downsampling
does not affect CSV measurements or verification.

The exported topology is retained. Floating cell R||C pairs use an equivalent
scaled state preserving R/(1+sRC); switches use the same ports with a finite
conductance edge. Commands use equivalent time expressions instead of forced
PWL breakpoints. The transient solves exact perturbations about the initial DC
state, retaining switched bias currents and restoring physical output offsets.
This avoids loss of precision from the large stack common-mode voltage. The cell impedance split, relaxation, package inductance,
switch capacitance and edge remain assumptions. No internal ADC or digital-filter
model is applied. This study does not establish register-read timing, a guaranteed
hardware wait, tolerance bounds, fast-edge protection qualification or ADC accuracy.
'''
    (REPORT/'README.md').write_text(text)
    write_json(REPORT/'provenance.json',dict(schema_version=1,study=config(),
        schematic_sha256=digest(SCH),export_sha256=digest(EXPORT),
        design_source_hashes=json.loads(META.read_text())['source_hashes'],
        parameters=json.loads((CASE/'circuit/wired-review.json').read_text()),
        implementation_hashes={p.name:digest(p) for p in CASE.glob('*.py')},
        run_inputs={c['id']:json.loads((RAW/c['id']/'inputs.json').read_text()) for c in cases()},
        solver_time_s=sum(x[2]['elapsed_s'] for x in values),
        artifacts={p.name:digest(p) for p in REPORT.iterdir() if p.is_file() and p.name!='provenance.json'}))
    print('Published',REPORT,flush=True)
