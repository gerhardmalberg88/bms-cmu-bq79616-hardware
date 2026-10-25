#!/usr/bin/env python3
"""Build a 16S prototype manufacturing package without editing design/.

Run with KiCad 10's Python (pcbnew), see tools/manufacturing-requirements.txt.
All intermediate files are under ignored build/. Never overwrite a published
release. --resume is only for completing the same unpublished source snapshot.
Copyright (C) 2021-2026 Gerhard Malberg; SPDX-License-Identifier: CERN-OHL-P-2.0
"""
import argparse
import collections
import concurrent.futures
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import struct
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / 'design'
BASE = 'battery_management_system_cell_monitoring_unit'
sys.path.insert(0, str(ROOT / 'build/python-deps'))
import pcbnew


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(ref):
    return (re.sub(r'\d', '', ref), int(re.search(r'\d+', ref)[0]))


def source_files():
    for p in DESIGN.rglob('*'):
        if not p.is_file() or any(x.startswith('.') or x.endswith('-backups') for x in p.relative_to(DESIGN).parts):
            continue
        if p.name.startswith('~') or p.suffix in ('.lck', '.lock', '.bak', '.kicad_prl') or p.name == 'fp-info-cache':
            continue
        yield p


def source_hashes():
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(source_files())}


def notice_files():
    return [ROOT/'LICENSE', ROOT/'NOTICE.md', *sorted((ROOT/'LICENSES').glob('*.txt'))]


def refresh_document_exports(out):
    """Keep supporting review exports synchronized with the checked release."""
    generated=ROOT/'docs/generated'
    shutil.copy2(out/'documentation/schematic.pdf',generated/'schematic.pdf')
    shutil.copy2(out/'verification/source.net',generated/'netlist.net')
    erc=json.loads((out/'verification/erc.json').read_text(encoding='utf-8'))
    violations=[v for sheet in erc['sheets'] for v in sheet['violations']]
    lines=['Supporting ERC summary; native report is in the dated manufacturing package.',
           'KiCad: '+erc['kicad_version'],'Check date: '+erc['date'],
           'Configured violations: '+str(len(violations)),
           'Existing ignored categories: '+', '.join(c['key'] for c in erc['ignored_checks']),
           'See supplemental-erc.json and readiness.md for the disabled-category audit.']
    (generated/'erc_report.rpt').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def copy_release_docs(out):
    """Rebase links in copied docs; full-repository references use the source ZIP."""
    docs=ROOT/'docs'
    # Remove renamed/deleted managed documents before rebuilding an unpublished
    # package. Native schematic.pdf and other export files are not managed here.
    destination_root=(out/'documentation').resolve()
    expected={p.relative_to(docs) for p in docs.rglob('*.md')}
    for old in destination_root.rglob('*.md'):
        if old.relative_to(destination_root) not in expected:
            assert old.resolve().is_relative_to(destination_root)
            old.unlink()
    for source in sorted(docs.rglob('*')):
        if not source.is_file():continue
        target=out/'documentation'/source.relative_to(docs)
        target.parent.mkdir(parents=True,exist_ok=True)
        if source.suffix!='.md':
            shutil.copy2(source,target);continue
        body=source.read_text(encoding='utf-8')
        def link(match):
            href=match.group(1)
            if re.match(r'\w+://|mailto:|#',href):return match.group(0)
            path,sep,anchor=href.partition('#')
            resolved=(source.parent/path).resolve()
            if resolved.is_relative_to(docs):
                destination=out/'documentation'/resolved.relative_to(docs)
            elif resolved.is_relative_to(out):destination=resolved
            elif resolved in notice_files():destination=out/resolved.relative_to(ROOT)
            else:
                destination=out/'verification/source-snapshot.zip';sep=anchor=''
            relative=Path(os.path.relpath(destination,target.parent)).as_posix()
            return ']('+relative+sep+anchor+')'
        body=re.sub(r'\]\(([^\s)]+)\)',link,body)
        target.write_text(body,encoding='utf-8')


def inventory(board):
    rows = []
    for f in board.GetFootprints():
        fields = {x.GetName(): x.GetText() for x in f.GetFields()}
        rows.append(dict(ref=f.GetReference(), value=f.GetValue(), dnp=f.IsDNP(),
                         exclude_bom=f.IsExcludedFromBOM(), exclude_pos=f.IsExcludedFromPosFiles(),
                         side=board.GetLayerName(f.GetLayer()), x=f.GetPosition().x/1e6,
                         y=f.GetPosition().y/1e6, rotation=f.GetOrientationDegrees(),
                         footprint=str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName()),
                         fields=fields, models=[m.m_Filename for m in f.Models() if m.m_Show],
                         pads=[dict(number=p.GetNumber(), net=p.GetNetname(), x=p.GetPosition().x/1e6,
                                    y=p.GetPosition().y/1e6) for p in f.Pads()]))
    return sorted(rows, key=lambda r:key(r['ref']))


def csv_write(path, headers, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        w=csv.writer(handle); w.writerow(headers); w.writerows(rows)


def binary_stl(path):
    raw=path.read_bytes()
    if len(raw)>=84 and len(raw)==84+50*struct.unpack_from('<I',raw,80)[0]:
        return
    normals=re.findall(rb'facet normal\s+([^\r\n]+)',raw)
    vertices=re.findall(rb'vertex\s+([^\r\n]+)',raw)
    assert len(vertices)==3*len(normals)
    output=bytearray(b'CMU rev0.1 16S; mm; native KiCad mesh converted to binary, no simplification'.ljust(80,b' '))
    output.extend(struct.pack('<I',len(normals)))
    for i,n in enumerate(normals):
        values=[float(x) for x in n.split()]+[float(x) for v in vertices[3*i:3*i+3] for x in v.split()]
        output.extend(struct.pack('<12fH',*values,0))
    path.write_bytes(output)


def filter_placement(out):
    path=out/'assembly/placement.csv'
    original=out/'verification/native-placement.csv'
    if not original.exists():shutil.copy2(path,original)
    with path.open(encoding='utf-8-sig') as h:
        reader=csv.DictReader(h);headers=reader.fieldnames;placements=list(reader)
    inventory_rows=json.loads((out/'verification/component-inventory.json').read_text())
    fitted={r['ref'] for r in inventory_rows if not r['exclude_bom'] and not r['dnp']}
    excluded={r['Ref'] for r in placements}-fitted
    assert excluded <= {'H1','H2','H3','H4'}
    selected=[r for r in placements if r['Ref'] in fitted]
    assert len(selected)==157
    csv_write(path,headers,[[r[k] for k in headers] for r in selected])


class Release:
    def __init__(self, args):
        self.args=args
        self.out=ROOT/'manufacturing'/('rev0.1-'+args.date)
        self.work=ROOT/'build'/('manufacturing-rev0.1-'+args.date)
        self.stage=self.work/'design'
        self.pcb=self.stage/(BASE+'.kicad_pcb')
        self.sch=self.stage/(BASE+'.kicad_sch')
        self.cli=Path(args.kicad_cli)
        self.env=dict(os.environ)
        self.env['KICAD_CONFIG_HOME']=str(self.work/'config')
        self.env['KICAD_DOCUMENTS_HOME']=str(self.work/'documents')
        for name in ('config','documents'):(self.work/name).mkdir(parents=True, exist_ok=True)
        self.env.setdefault('KICAD10_3DMODEL_DIR',str(self.cli.parent.parent/'share/kicad/3dmodels'))
        self.env.setdefault('KICAD10_FOOTPRINT_DIR',str(self.cli.parent.parent/'share/kicad/footprints'))
        self.env.setdefault('KICAD10_SYMBOL_DIR',str(self.cli.parent.parent/'share/kicad/symbols'))
        config=self.work/'config/10.0';config.mkdir(parents=True,exist_ok=True)
        for filename,rootnode in [('sym-lib-table','sym_lib_table'),('fp-lib-table','fp_lib_table')]:
            template=(self.cli.parent.parent/'share/kicad/template'/filename).as_posix()
            (config/filename).write_text(f'({rootnode}\n (version 7)\n (lib (name "KiCad") (type "Table") (uri "{template}") (options "") (descr "KiCad Default Libraries"))\n)\n',encoding='utf-8')

    def run(self, label, args, expected=(0,)):
        cmd=[str(self.cli)]+list(map(str,args))
        result=subprocess.run(cmd,cwd=self.stage,env=self.env,capture_output=True,text=True,encoding='utf-8',errors='replace')
        dump(self.out/'verification/logs'/(label+'.json'),dict(command=cmd,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr))
        print(label, result.returncode, result.stdout[-350:].strip(), flush=True)
        if result.returncode not in expected: raise RuntimeError(label+' failed; see verification/logs')
        return result

    def unchanged(self):
        original=json.loads((self.out/'verification/source-sha256.json').read_text(encoding='utf-8'))
        if source_hashes()!=original:raise RuntimeError('Source changed since snapshot: start a new release build.')

    def prepare(self):
        if self.out.exists() and not self.args.resume:raise RuntimeError('Output exists; use a new date or --resume for an unpublished build.')
        if (self.out/'verification/source-sha256.json').exists():
            self.unchanged()
            if (self.out/'verification/prepare-complete.json').exists():
                print('Existing snapshot matches; prepare skipped.',flush=True);return
        for name in ('fabrication','assembly','procurement','documentation','3d','verification'):(self.out/name).mkdir(parents=True, exist_ok=True)
        before=source_hashes()
        for p in source_files():
            dest=self.stage/p.relative_to(DESIGN);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        if source_hashes()!=before:raise RuntimeError('Source changed while snapshotting.')
        dump(self.out/'verification/source-sha256.json',before)
        board=pcbnew.LoadBoard(str(self.pcb))
        rows=inventory(board)
        dump(self.out/'verification/component-inventory.json',rows)
        fitted=[r for r in rows if not r['exclude_bom'] and not r['dnp']]
        dnp=[r for r in rows if not r['exclude_bom'] and r['dnp']]
        assert len(rows)==198 and len(fitted)==157 and len(dnp)==37, 'Population changed: review configuration.'
        assert all(r['side']=='F.Cu' for r in fitted)
        assert all(r['fields'].get('MPN') and r['fields'].get('digikey_pn') for r in fitted+dnp)
        model_records=[]
        for model in sorted({m for r in rows for m in r['models']}):
            resolved=model.replace('${KIPRJMOD}',str(self.stage)).replace('${KICAD10_3DMODEL_DIR}',self.env['KICAD10_3DMODEL_DIR'])
            p=Path(resolved)
            assert p.exists(), 'Missing model '+resolved
            model_records.append(dict(model=model,sha256=sha(p),bytes=p.stat().st_size))
        dump(self.out/'verification/3d-models.json',model_records)
        # Exact outline extremes, excluding Edge.Cuts stroke: 99 x 61 mm.
        edges=[s for s in board.GetDrawings() if s.GetLayer()==pcbnew.Edge_Cuts]
        xs=[v.x/1e6 for s in edges for v in (s.GetStart(),s.GetEnd())]
        ys=[v.y/1e6 for s in edges for v in (s.GetStart(),s.GetEnd())]
        self.origin=[min(xs),max(ys)]
        assert abs(max(xs)-min(xs)-99)<1e-6 and abs(max(ys)-min(ys)-61)<1e-6
        board.GetDesignSettings().SetAuxOrigin(pcbnew.VECTOR2I(pcbnew.FromMM(self.origin[0]),pcbnew.FromMM(self.origin[1])))
        board.GetPlotOptions().SetUseAuxOrigin(True)
        board.GetPlotOptions().SetCreateGerberJobFile(True)
        pcbnew.SaveBoard(str(self.pcb),board)
        dump(self.out/'verification/export-origin.json',dict(source_xy_mm=self.origin,export_axes='X right, Y up, Z out of top',outline_mm=[99,61],scope='Staging copy only; authoritative source untouched'))
        self.run('erc',['sch','erc','--format','json','--severity-all','--exit-code-violations','-o',self.out/'verification/erc.json',self.sch])
        self.run('drc',['pcb','drc','--format','json','--severity-all','--all-track-errors','--schematic-parity','--refill-zones','--save-board','--exit-code-violations','-o',self.out/'verification/drc.json',self.pcb])
        filled=pcbnew.LoadBoard(str(self.pcb))
        assert inventory(filled)==rows, 'Export preparation changed footprint/pad data.'
        # Supplemental audit: temporarily enable ignored categories in snapshot.
        project=self.stage/(BASE+'.kicad_pro'); saved=project.read_bytes();pro=json.loads(saved)
        ignored=[]
        for domain in ('erc','drc'):
            report=json.loads((self.out/'verification'/f'{domain}.json').read_text(encoding='utf-8'))
            ignored.extend(dict(domain=domain,**x) for x in report.get('ignored_checks',[]))
        dump(self.out/'verification/disabled-checks.json',ignored)
        for group in (pro.get('erc',{}).get('rule_severities',{}),pro.get('board',{}).get('design_settings',{}).get('rule_severities',{})):
            for k,v in list(group.items()):
                if v=='ignore':group[k]='warning'
        try:
            dump(project,pro)
            self.run('supplemental-erc',['sch','erc','--format','json','--severity-all','-o',self.out/'verification/supplemental-erc.json',self.sch])
            self.run('supplemental-drc',['pcb','drc','--format','json','--severity-all','--schematic-parity','-o',self.out/'verification/supplemental-drc.json',self.pcb])
        finally:project.write_bytes(saved)
        self.run('netlist',['sch','export','netlist','--format','kicadsexpr','-o',self.out/'verification/source.net',self.sch])
        self.unchanged()
        dump(self.out/'verification/prepare-complete.json',dict(source_unchanged=True))

    def exports(self):
        self.unchanged()
        fab=self.out/'fabrication';asm=self.out/'assembly'
        layers='F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,In5.Cu,In6.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,Edge.Cuts'
        self.run('gerbers',['pcb','export','gerbers','--layers',layers,'--use-drill-file-origin','--precision','6','--check-zones','-o',str(fab)+os.sep,self.pcb])
        self.run('drills',['pcb','export','drill','--format','excellon','--drill-origin','plot','--excellon-units','mm','--excellon-zeros-format','decimal','--excellon-oval-format','route','--excellon-separate-th','--generate-map','--map-format','pdf','--generate-report','--report-path',fab/'drill-report.txt','-o',str(fab)+os.sep,self.pcb])
        self.run('electrical-test',['pcb','export','ipcd356','-o',fab/'electrical-test.d356',self.pcb])
        self.run('placement',['pcb','export','pos','--format','csv','--units','mm','--side','both','--exclude-dnp','--use-drill-file-origin','-o',asm/'placement.csv',self.pcb])
        filter_placement(self.out)
        self.run('assembly-top',['pcb','export','pdf','--layers','F.Fab,F.Silkscreen,Edge.Cuts','--mode-single','--scale','3','--black-and-white','--crossout-DNP-footprints-on-fab-layers','--include-border-title','-o',asm/'assembly-top.pdf',self.pcb])
        self.run('assembly-bottom',['pcb','export','pdf','--layers','B.Fab,B.Silkscreen,Edge.Cuts','--mode-single','--scale','3','--black-and-white','--mirror','--include-border-title','-o',asm/'assembly-bottom.pdf',self.pcb])
        self.run('fabrication-drawing',['pcb','export','pdf','--layers','Edge.Cuts,Dwgs.User','--mode-single','--scale','3','--black-and-white','--include-border-title','-o',fab/'board-drawing.pdf',self.pcb])
        self.run('schematic-pdf',['sch','export','pdf','--no-background-color','-o',self.out/'documentation/schematic.pdf',self.sch])
        # Stencil-only board removes paste apertures from DNP pads, no source edit.
        paste=pcbnew.LoadBoard(str(self.pcb));removed=[]
        for f in paste.GetFootprints():
            if f.IsDNP():
                for p in f.Pads():
                    ls=p.GetLayerSet()
                    if ls.Contains(pcbnew.F_Paste) or ls.Contains(pcbnew.B_Paste):removed.append([f.GetReference(),p.GetNumber()])
                    ls.RemoveLayer(pcbnew.F_Paste);ls.RemoveLayer(pcbnew.B_Paste);p.SetLayerSet(ls)
        stencil=self.stage/(BASE+'-stencil.kicad_pcb');pcbnew.SaveBoard(str(stencil),paste)
        self.run('stencil',['pcb','export','gerbers','--layers','F.Paste','--use-drill-file-origin','-o',str(asm/'stencil')+os.sep,stencil])
        dump(self.out/'verification/stencil-DNP-omissions.json',removed)
        jobs=[('assembly-step','step',self.out/'3d/CMU-rev0.1-16S.step',[]),
              ('board-step','step',self.out/'3d/CMU-rev0.1-board.step',['--board-only']),
              ('assembly-stl','stl',self.out/'3d/CMU-rev0.1-16S.stl',[])]
        def model(job):
            label,fmt,path,extra=job
            return self.run(label,['pcb','export',fmt,'--force','--no-dnp','--subst-models','--drill-origin','--cut-vias-in-body','-o',path]+extra+[self.pcb])
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(model,jobs))
        binary_stl(self.out/'3d/CMU-rev0.1-16S.stl')
        self.unchanged()

    def bom(self):
        import xlsxwriter
        rows=json.loads((self.out/'verification/component-inventory.json').read_text(encoding='utf-8'))
        mapping=json.loads((ROOT/'tools/digikey-packaging.json').read_text(encoding='utf-8'))
        for m in mapping.values():
            m.setdefault('packaging','Cut Tape (CT)')
            m.setdefault('verification_date','2026-10-24')
            m.setdefault('verification_basis','DigiKey public product listing; stock/prices are not a live quote')
        grouped=collections.defaultdict(list)
        for r in rows:
            if not r['exclude_bom']:grouped[(r['fields']['MPN'],r['dnp'])].append(r)
        headers=['References','Quantity','Manufacturer','MPN','Value','Footprint','Assembly status','Saved DigiKey SKU','Order DigiKey SKU','Product URL','Verification','Assembly condition']
        allrows=[]
        for (mpn,dnp),rs in sorted(grouped.items()):
            m=mapping[mpn];r=rs[0]
            allrows.append([', '.join(x['ref'] for x in rs),len(rs),m['manufacturer'],mpn,r['value'],r['footprint'],
                            'PURCHASE, DO NOT POPULATE' if dnp else 'FIT',r['fields']['digikey_pn'],m['sku'],m['url'],m.get('note','MPN and packaging verified'),
                            '; '.join(sorted({x['fields'].get('Assembly condition','') for x in rs} - {''}))])
        fitted=[r for r in allrows if r[6]=='FIT'];dnp=[r for r in allrows if r[6]!='FIT']
        assert sum(r[1] for r in fitted)==157 and sum(r[1] for r in dnp)==37
        for name,data in [('bom-fitted',fitted),('bom-DNP-purchase-only',dnp),('bom-all-board-positions',allrows)]:
            csv_write(self.out/'assembly'/(name+'.csv'),headers,data)
        csv_write(ROOT/'docs/generated/bom.csv',headers,allrows)
        book=xlsxwriter.Workbook(str(self.out/'assembly/bom.xlsx'))
        for name,data in [('Fitted 16S',fitted),('DNP - purchase only',dnp),('All board positions',allrows)]:
            ws=book.add_worksheet(name);ws.write_row(0,0,headers)
            for i,r in enumerate(data,1):ws.write_row(i,0,r)
            ws.freeze_panes(1,0);ws.autofilter(0,0,len(data),len(headers)-1);ws.set_column(0,0,52);ws.set_column(2,11,28)
        book.close()
        # One row per exact MPN. DNP status remains explicit in references and workbook.
        importheaders=['DigiKey Part Number','Quantity','Customer Reference','Manufacturer','Manufacturer Part Number','Assembly Status']
        imports=[[r[8],r[1],('DNP - ' if r[6]!='FIT' else '')+r[0],r[2],r[3],r[6]] for r in allrows]
        csv_write(self.out/'procurement/digikey-import.csv',importheaders,imports)
        book=xlsxwriter.Workbook(str(self.out/'procurement/digikey-order.xlsx'))
        bold=book.add_format({'bold':True,'bg_color':'#DCE6F1'});inputfmt=book.add_format({'bg_color':'#FFF2CC','num_format':'0'})
        ws=book.add_worksheet('Settings');ws.write_row(0,0,['Setting','Value','Notes'],bold)
        ws.write_row(1,0,['Board count',1,'Default: one board; DNP parts purchased but NOT fitted'])
        ws.write(1,1,1,inputfmt);ws.data_validation(1,1,1,1,{'validate':'integer','criteria':'>=','value':1})
        ws.write_row(3,0,['Usage','Upload DigiKey Import sheet or supplied CSV.','After edits, export that sheet as CSV; supplied CSV remains the one-board baseline.'])
        ws.write_row(5,0,['Packaging','Same exact MPN, cut tape/single pieces where verified.','No substitute MPNs; check live stock and MOQ at order time.'])
        ws.set_column(0,0,22);ws.set_column(1,1,65);ws.set_column(2,2,95)
        order=book.add_worksheet('Order calculation')
        order.write_row(0,0,['MPN','DigiKey SKU','Qty per board','Additional spares','Order quantity','References','Assembly status','Manufacturer','Original SKU','Product URL','Verification'],bold)
        imp=book.add_worksheet('DigiKey Import');imp.write_row(0,0,importheaders,bold)
        for i,(r,impdata) in enumerate(zip(allrows,imports),1):
            order.write_row(i,0,[r[3],r[8],r[1],0]);order.write(i,3,0,inputfmt)
            order.write_formula(i,4,f'=C{i+1}*Settings!$B$2+D{i+1}',None,r[1])
            order.write_row(i,5,[r[0],r[6],r[2],r[7],r[9],r[10]])
            imp.write_row(i,0,impdata);imp.write_formula(i,1,f"='Order calculation'!E{i+1}",None,r[1])
        order.data_validation(1,3,len(allrows),3,{'validate':'integer','criteria':'>=','value':0})
        for sheet in (order,imp):sheet.freeze_panes(1,0);sheet.set_column(0,10,29)
        order.set_column(5,5,75);order.autofilter(0,0,len(allrows),10);imp.autofilter(0,0,len(allrows),5)
        book.close()
        dump(self.out/'procurement/part-verification.json',mapping)
        dump(self.out/'verification/population-check.json',dict(fitted=157,DNP_purchased_not_fitted=37,purchased=194,purchase_MPNs=len(imports),fitted_MPNs=len(fitted),spares=0,boards=1))

    def render(self):
        """Ray-trace the fitted assembly using a disposable rendering copy."""
        self.unchanged()
        render_dir=self.work/'render/design'
        for p in source_files():
            dest=render_dir/p.relative_to(DESIGN)
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(p,dest)
        board=pcbnew.LoadBoard(str(self.pcb))
        expected=json.loads((self.out/'verification/component-inventory.json').read_text())
        assert inventory(board)==expected, 'Snapshot population differs from release'
        shown=[];omitted=[]
        for footprint in board.GetFootprints():
            if footprint.IsDNP():
                footprint.Models().clear()
                omitted.append(footprint.GetReference())
            elif not footprint.IsExcludedFromBOM():
                assert any(m.m_Show for m in footprint.Models()), footprint.GetReference()
                shown.append(footprint.GetReference())
        assert len(shown)==157 and len(omitted)==37
        render_board=render_dir/(BASE+'.kicad_pcb')
        pcbnew.SaveBoard(str(render_board),board)
        config=self.work/'config/10.0/3d_viewer.json'
        settings=json.loads(config.read_text()) if config.exists() else {}
        settings.setdefault('render',{})['show_footprints_dnp']=False
        settings['use_stackup_colors']=True
        settings['layer_presets']=[dict(name='CMU neutral',
            layers=['board','plated_barrels','copper','copper_bottom',
                    'silkscreen_top','silkscreen_bottom','soldermask_top',
                    'soldermask_bottom','solderpaste','th_models','smd_models',
                    'virtual_models','non_pos_file_models','fp_references','fp_text'],
            colors=[dict(layer='background_top',color='rgb(225, 225, 225)'),
                    dict(layer='background_bottom',color='rgb(165, 165, 165)')])]
        dump(config,settings)
        output=self.out/'3d/CMU-rev0.1-16S-raytraced.png'
        from PIL import Image
        # KiCad 10.0.4 rounds its ray-packet buffer dimensions. A requested
        # 2432 x 1632 produces 2408 x 1600 here. Trim only the empty border to
        # exact delivery size: no resampling, model changes or synthetic pixels.
        raw=self.work/'render/native-raytraced.png'
        result=self.run('pcb-raytrace',['pcb','render','--width','2432',
            '--height','1632','--side','top','--quality','high',
            '--background','opaque','--preset','CMU neutral',
            '--perspective','--rotate','325,0,25','--zoom','1','-o',raw,render_board])
        with Image.open(raw) as img:
            actual=list(img.size)
            assert actual[0]>=2400 and actual[1]>=1600
            left=(actual[0]-2400)//2;top=(actual[1]-1600)//2
            crop=[left,top,left+2400,top+1600]
            img.crop(crop).save(output)
        dump(self.out/'verification/pcb-render.json',dict(renderer='KiCad native ray tracer',
             image=output.relative_to(self.out).as_posix(),sha256=sha(output),pixels=[2400,1600],
             fitted_references=sorted(shown,key=key),omitted_DNP_references=sorted(omitted,key=key),
             view='Angled top, perspective; rotation -35,0,25 degrees',
             background='Neutral grey',stackup_colors=True,native_command=result.args,
             native_pixels=actual,native_sha256=sha(raw),crop_box=crop,
             postprocess='Lossless empty-border crop only; no resampling or synthetic content',
             source_unchanged=True,scope='DNP models removed only from disposable rendering copy'))
        self.unchanged()

    def finalize(self):
        self.unchanged()
        from pypdf import PdfReader
        assert len(PdfReader(self.out/'documentation/schematic.pdf').pages)==7
        with (self.out/'assembly/placement.csv').open(encoding='utf-8-sig') as h:places=list(csv.DictReader(h))
        rows=json.loads((self.out/'verification/component-inventory.json').read_text())
        expected={r['ref']:r for r in rows if not r['exclude_bom'] and not r['dnp']}
        assert {r['Ref'] for r in places}==set(expected), 'Placement population mismatch'
        origin=json.loads((self.out/'verification/export-origin.json').read_text())['source_xy_mm']
        for r in places:
            f=expected[r['Ref']]
            assert abs(float(r['PosX'])-(f['x']-origin[0]))<0.00001
            assert abs(float(r['PosY'])-(origin[1]-f['y']))<0.00001
            assert r['Side']=='top'
            assert abs((float(r['Rot'])-f['rotation']+180)%360-180)<0.00001
        stl=self.out/'3d/CMU-rev0.1-16S.stl'
        assert stl.stat().st_size<10_000_000, 'STL exceeds GitHub preview limit'
        from release_documents import write_documents
        write_documents(self)
        refresh_document_exports(self.out)
        # Keep exact source snapshot available without including scratch files.
        with zipfile.ZipFile(self.out/'verification/source-snapshot.zip','w',zipfile.ZIP_DEFLATED) as z:
            for p in sorted(source_files()):z.write(p,p.relative_to(ROOT).as_posix())
            for p in sorted((ROOT/'tools').iterdir()):
                if p.is_file() and p.suffix in ('.py','.cpp','.h','.json','.txt'):z.write(p,p.relative_to(ROOT).as_posix())
            for p in notice_files()+[ROOT/'README.md',ROOT/'.gitignore',ROOT/'.gitattributes']:
                z.write(p,p.relative_to(ROOT).as_posix())
            for folder in ('docs','sim'):
                for p in sorted((ROOT/folder).rglob('*')):
                    if not p.is_file() or any(x in ('results','vendor','__pycache__') for x in p.relative_to(ROOT/folder).parts):continue
                    z.write(p,p.relative_to(ROOT).as_posix())
        copy_release_docs(self.out)
        for folder in (self.out,self.out/'fabrication'):
            for p in notice_files():
                dest=folder/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(p,dest)
        version=subprocess.run([str(self.cli),'version'],capture_output=True,text=True,env=self.env).stdout.strip()
        import importlib.metadata
        dump(self.out/'verification/tooling.json',dict(python=sys.version,kicad=version,
             packages={n:importlib.metadata.version(n) for n in ('xlsxwriter','reportlab','pypdf','pygerber','numpy','pillow')},
             script_sha256={p.name:sha(p) for p in sorted((ROOT/'tools').iterdir()) if p.is_file()}))
        commit=subprocess.run(['git','rev-parse','--verify','HEAD'],cwd=ROOT,capture_output=True,text=True)
        dump(self.out/'manifest.json',dict(board='BMS CMU BQ79616-Q1',revision='0.1',variant='16S',export_date=self.args.date,
             design_issue_date='2026-09-04',manufacturer='Eurocircuits',kicad_version=version,
             source_commit=commit.stdout.strip() if commit.returncode==0 else None,
             provenance='Exact source hashes and source-snapshot.zip; uncommitted working tree',
             fitted_components=157,DNP_purchased_not_fitted=37,purchase_quantity=194,
             status='Prototype manufacturing package; supplier/process and engineering confirmations remain open',
             source_unchanged=True,origin=origin,units='mm',ipc_d356_units='CUST 0: 0.0001 inch'))
        for archive,folder in [('fabrication.zip',self.out/'fabrication')]:
            with zipfile.ZipFile(self.out/archive,'w',zipfile.ZIP_DEFLATED) as z:
                for p in sorted(folder.rglob('*')):
                    if p.is_file():z.write(p,p.relative_to(folder).as_posix())
        files=[p for p in sorted(self.out.rglob('*')) if p.is_file() and p.name not in ('SHA256SUMS','complete-package.zip','complete-package.zip.sha256')]
        (self.out/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.relative_to(self.out).as_posix()+'\n' for p in files),encoding='utf-8')
        archive=self.out/'complete-package.zip'
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for p in files+[self.out/'SHA256SUMS']:z.write(p,p.relative_to(self.out).as_posix())
        (self.out/'complete-package.zip.sha256').write_text(sha(archive)+'  complete-package.zip\n',encoding='ascii')
        self.unchanged()
        print('Package finalized:',self.out,flush=True)

    def audit(self):
        from audit_manufacturing import audit
        audit(self)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--date',required=True,help='Actual local export date YYYY-MM-DD')
    p.add_argument('--phase',choices=['prepare','exports','bom','audit','render','finalize','all'],default='all')
    p.add_argument('--resume',action='store_true')
    p.add_argument('--kicad-cli',default='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
    p.add_argument('--freecad-python',default='C:/Program Files/FreeCAD 1.1/bin/python.exe')
    args=p.parse_args()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',args.date):p.error('Invalid date')
    r=Release(args)
    for phase in (['prepare','exports','bom','audit','render','finalize'] if args.phase=='all' else [args.phase]):getattr(r,phase)()


if __name__=='__main__':main()
