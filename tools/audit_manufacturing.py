"""Independent readback checks for the exported prototype package.
Copyright (C) 2021-2026 Gerhard Malberg; SPDX-License-Identifier: CERN-OHL-P-2.0
"""
import collections
import concurrent.futures
import csv
from dataclasses import asdict
import json
import math
from pathlib import Path
import re
import struct
import subprocess
import sys


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, default=str)+'\n',encoding='utf-8')


def normalize_ipc(release):
    """Repair KiCad 10.0.4's invalid via soldermask field using actual tenting.

    Native geometry/net names are kept; only the soldermask field and record
    padding are normalized. CUST 0 is intentionally retained (0.0001 inch).
    Record meaning follows KiCad's exporter documentation/source:
    https://gitlab.com/kicad/code/kicad/-/blob/master/pcbnew/exporters/export_d356.cpp
    """
    import pcbnew
    board=pcbnew.LoadBoard(str(release.pcb))
    path=release.out/'fabrication/electrical-test.d356'
    raw=path.read_bytes();lines=raw.decode('ascii').splitlines()
    original=release.out/'verification/ipc-native-export.txt'
    if not original.exists():original.write_bytes(raw)
    origin=board.GetDesignSettings().GetAuxOrigin()
    vias={}
    for v in board.GetTracks():
        if not isinstance(v,pcbnew.PCB_VIA):continue
        x=(v.GetPosition().x-origin.x)/1e6/0.00254
        y=(origin.y-v.GetPosition().y)/1e6/0.00254
        vias[(round(x),round(y))]=int(v.IsTented(pcbnew.F_Mask))+2*int(v.IsTented(pcbnew.B_Mask))
    output=[];changed=0
    for line in lines:
        if line.startswith(('317','327','367')):
            mask=int(re.search(r'S(-?\d+)\s*$',line)[1])
            if line[20:26].strip()=='VIA':
                loc=re.search(r'A\d{2}X([+-]\d{6})Y([+-]\d{6})',line)
                xy=(int(loc[1]),int(loc[2]))
                # Native integer conversion can differ by one decimil at ties.
                candidates=[m for (x,y),m in vias.items() if abs(x-xy[0])<=1 and abs(y-xy[1])<=1]
                assert len(candidates)==1,'Ambiguous IPC via match'
                actual=candidates[0]
                if mask!=actual:changed+=1
                mask=actual
            assert mask in range(4)
            assert re.fullmatch(r'.{71}\s*S-?\d+\s*',line)
            line=(line[:71]+' S'+str(mask)).ljust(80)
        else:line=line.ljust(80)
        assert len(line)==80
        output.append(line)
    path.write_text('\n'.join(output)+'\n',encoding='ascii')
    write_json(release.out/'verification/ipc-normalization.json',dict(native_version='10.0.4',
        invalid_via_mask_fields_corrected=len(re.findall(rb'S-?\d{2,}',original.read_bytes())),via_count=len(vias),
        correction='Soldermask fields from actual via tenting; correct blank/padding to 80 columns. Geometry/net tokens retained.',
        units='CUST 0: 0.0001 inch (native IPC export); same origin as mm fabrication data',
        reference='https://gitlab.com/kicad/code/kicad/-/blob/master/pcbnew/exporters/export_d356.cpp'))


def audit(release):
    import pcbnew
    import numpy as np
    from pygerber.gerberx3.api.v2 import GerberFile
    out=release.out;v=out/'verification';fab=out/'fabrication'
    normalize_ipc(release)
    rows=json.loads((v/'component-inventory.json').read_text())
    board=pcbnew.LoadBoard(str(release.pcb));origin=board.GetDesignSettings().GetAuxOrigin()
    # Read drills independently and compare every position and diameter.
    expected=[]
    for obj in board.GetTracks():
        if isinstance(obj,pcbnew.PCB_VIA):expected.append((obj.GetPosition(),obj.GetDrillValue()))
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetDrillSize().x:
                assert p.GetDrillSize().x==p.GetDrillSize().y,'Review slot export'
                expected.append((p.GetPosition(),p.GetDrillSize().x))
    expected=collections.Counter((round((p.x-origin.x)/1e6,6),round((origin.y-p.y)/1e6,6),round(d/1e6,6)) for p,d in expected)
    actual=collections.Counter();tools={};tool=None
    for path in sorted(fab.glob('*.drl')):
        text=path.read_text();assert 'METRIC' in text
        for line in text.splitlines():
            m=re.fullmatch(r'T(\d+)C([\d.]+)',line)
            if m:tools[m[1]]=float(m[2]);continue
            m=re.fullmatch(r'T(\d+)',line)
            if m:tool=m[1];continue
            m=re.fullmatch(r'X([\d.-]+)Y([\d.-]+)',line)
            if m:actual[(round(float(m[1]),6),round(float(m[2]),6),round(tools[tool],6))]+=1
    remaining=list(actual.elements());max_drill_error=0.0
    for x,y,d in expected.elements():
        matches=[(i,max(abs(x-a),abs(y-b))) for i,(a,b,c) in enumerate(remaining) if abs(d-c)<1e-6 and max(abs(x-a),abs(y-b))<=0.000501]
        assert len(matches)==1,'Drill data mismatch (beyond Excellon 0.001 mm resolution)'
        i,err=matches[0];max_drill_error=max(max_drill_error,err);remaining.pop(i)
    assert not remaining
    # STEP occurrence labels must represent exactly the fitted reference set.
    fitted={r['ref'] for r in rows if not r['exclude_bom'] and not r['dnp']}
    step=(out/'3d/CMU-rev0.1-16S.step').read_text()
    names=set(re.findall(r"NEXT_ASSEMBLY_USAGE_OCCURRENCE\('[^']*','([A-Z]+\d+)'",step))
    assert names==fitted,dict(missing=sorted(fitted-names),extra=sorted(names-fitted))
    mesh=(out/'3d/CMU-rev0.1-16S.stl').read_bytes();count=struct.unpack_from('<I',mesh,80)[0]
    assert len(mesh)==84+count*50 and len(mesh)<10_000_000
    dtype=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attribute','<u2')])
    triangles=np.frombuffer(mesh,dtype=dtype,offset=84,count=count)['vertices']
    assert np.isfinite(triangles).all()
    bb=[triangles.min(axis=(0,1)).tolist(),triangles.max(axis=(0,1)).tolist()]
    assert abs(bb[1][0]-bb[0][0]-99)<0.001 and abs(bb[1][1]-bb[0][1]-61)<0.001
    # PCB pins/vias must retain an identical net partition in the IPC export.
    full={r['ref']:r for r in rows};netmap=collections.defaultdict(set);reverse=collections.defaultdict(set);records=0
    via_list=[x for x in board.GetTracks() if isinstance(x,pcbnew.PCB_VIA)]
    for line in (fab/'electrical-test.d356').read_text().splitlines():
        if not line.startswith(('317','327','367')):continue
        records+=1;net=line[3:17].strip();ref=line[20:26].strip();pin=line[27:31].strip()
        loc=re.search(r'A\d{2}X([+-]\d{6})Y([+-]\d{6})',line)
        x=float(loc[1])*0.00254+origin.x/1e6;y=origin.y/1e6-float(loc[2])*0.00254
        if ref=='VIA':
            pts=[p for p in via_list if abs(p.GetPosition().x/1e6-x)<0.003 and abs(p.GetPosition().y/1e6-y)<0.003]
            assert len(pts)==1;source_net=pts[0].GetNetname()
        else:
            pts=[p for p in full[ref]['pads'] if p['number']==pin and abs(p['x']-x)<0.003 and abs(p['y']-y)<0.003]
            assert len(pts)==1;source_net=pts[0]['net']
        if source_net:
            netmap[source_net].add(net);reverse[net].add(source_net)
    assert all(len(x)==1 for x in netmap.values()) and all(len(x)==1 for x in reverse.values()),'IPC net alias collision'
    assert records==912
    # Parse all plotted files independently. Render the actual Gerbers for CAM review.
    image_dir=v/'gerber-previews';image_dir.mkdir(exist_ok=True)
    paths=[p for p in fab.iterdir() if p.suffix in ('.gtl','.gbl','.g1','.g2','.g3','.g4','.g5','.g6','.gts','.gbs','.gto','.gm1')]
    paths+=list((out/'assembly/stencil').glob('*.gtp'))
    def render(path):
        parsed=GerberFile.from_file(path).parse()
        parsed.render_raster(image_dir/(path.stem+'.png'),dpmm=12)
        print('CAM readback:',path.name,flush=True)
        return dict(file=path.relative_to(out).as_posix(),**{k:float(n) for k,n in asdict(parsed.get_info()).items()})
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:gerbers=list(pool.map(render,paths))
    assert len(gerbers)==13
    job=json.loads(next(fab.glob('*.gbrjob')).read_text())
    assert job['GeneralSpecs']['LayerNumber']==8
    assert all((fab/x['Path']).exists() for x in job['FilesAttributes'])
    # Existing native STEP readback: independently load with FreeCAD/OpenCascade.
    code='''import json,sys\nfrom pathlib import Path\nimport FreeCAD,Part\np=Path(sys.argv[1]); result={}\nfor f in sorted((p/'3d').glob('*.step')):\n s=Part.Shape();s.read(str(f));b=s.BoundBox\n assert s.isValid()\n result[f.name]={'valid':True,'solids':len(s.Solids),'bbox_mm':[b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]}\n(p/'verification/step-geometry.json').write_text(json.dumps(result,indent=2)+'\\n')\n'''
    freecad=Path(release.args.freecad_python)
    subprocess.run([str(freecad),'-c',code,str(out)],check=True,capture_output=True,text=True)
    geometry=json.loads((v/'step-geometry.json').read_text())
    stepbb=geometry['CMU-rev0.1-16S.step']['bbox_mm']
    assert all(abs(a-b)<0.001 for a,b in zip(bb[0]+bb[1],stepbb))
    report=dict(drills_match_source=True,drill_max_coordinate_quantization_mm=max_drill_error,plated_holes=sum(actual.values()),nonplated_holes=0,
         placement_and_drill_origin_mm=[origin.x/1e6,origin.y/1e6],
         step_population_matches_fitted_BOM=True,step_component_occurrences=len(names),
         stl_facets=count,stl_bytes=len(mesh),stl_bbox_mm=bb,stl_mesh_simplified=False,
         step_stl_bounds_match=True,ipc_records=records,ipc_pin_net_partition_matches=True,
         ipc_native_units='0.0001 inch; converted during readback to compare with mm board',
         gerbers=gerbers,source_unchanged=True)
    write_json(v/'export-readback.json',report)
    release.unchanged()
    return report


if __name__=='__main__':
    from manufacturing_release import Release
    import argparse
    args=argparse.Namespace(date=sys.argv[1],resume=True,kicad_cli='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe',freecad_python='C:/Program Files/FreeCAD 1.1/bin/python.exe')
    audit(Release(args))
