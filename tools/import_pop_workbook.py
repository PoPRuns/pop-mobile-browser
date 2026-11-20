#!/usr/bin/env python3
"""Convert the author-supplied PoP XLSM research catalogue to static website JSON.

Uses artifact_tool; no Excel macros, JAR files, or binaries are embedded.
"""
import argparse, collections, json, re
from pathlib import Path
from artifact_tool import Blob, SpreadsheetFile

COLLECTIONS = [
 ('Harem Adventures','harem-adventures','Prince of Persia: Harem Adventures','2003–2004','Early mobile Prince of Persia editions and device variants.'),
 ('SoT','sands-of-time','Prince of Persia: The Sands of Time','2003','Explore the Sands of Time Java ME releases.'),
 ('WW','warrior-within','Prince of Persia: Warrior Within','2004','Warrior Within releases across Java-enabled phones.'),
 ('T2T','two-thrones','Prince of Persia: The Two Thrones','2005','The Two Thrones mobile versions and their many builds.'),
 ('Classic','classic','Prince of Persia: Classic','2007','Classic reimagined for Java ME devices.'),
 ('Classic + T2T','classic-two-thrones','Prince of Persia: Classic + The Two Thrones','2007','The two-in-one mobile pack.'),
 ('2008','prince-2008','Prince of Persia (2008)','2008','The 2008 mobile adaptation.'),
 ('TFS','forgotten-sands','Prince of Persia: The Forgotten Sands','2010','The Forgotten Sands across phones, languages and devices.'),
 ('Needs review','needs-review','Needs review','—','Unclassified related files, experiments and versions requiring research.'),
]
FIELDS=['group','name','displayTitle','version','vendor','cldc','midp','resolution','language',
        'aboutName','aboutVersion','aboutAuthor','sourceFilenames','oldFilename','archivePaths',
        'urls','device','notesGeneral','notesGameplay','notesGameplay2','size','crc32','sha1','sha256']
HEX64=re.compile('[0-9a-fA-F]{64}\\Z')
HEX40=re.compile('[0-9a-fA-F]{40}\\Z')
URL=re.compile(r'https?://[^\s\r\n]+')

def as_text(value):
    return '' if value is None else str(value).strip()

def convert(input_path, output):
    w=SpreadsheetFile.import_xlsx(Blob.load(str(input_path)))
    games=[]; builds=[]; groups=[]; related_files=[]; hashes=set(); errors=[]
    for sheet_name,slug,title,year,description in COLLECTIONS:
        s=w.worksheets.get_item(sheet_name)
        rows=s.get_range('A1:X210').values
        headers={as_text(v).lower():i for i,v in enumerate(rows[0]) if v}
        col={
          'group':'Gameplay Group (experimental)', 'name':'Applet Name', 'displayTitle':'Title Screen Name',
          'version':'Applet Version','vendor':'Applet Author','cldc':'CLDC','midp':'MIDP',
          'resolution':'Screen Dimension','language':'Language','aboutName':'About section Name',
          'aboutVersion':'About section Version','aboutAuthor':'About section Author',
          'sourceFilenames':'Source filenames','oldFilename':'File name (according to old zip)',
          'archivePaths':'Archive paths','urls':'Internet Archive URLs','device':'Device(s)',
          'notesGeneral':'Notes (general)','notesGameplay':'Notes (gameplay)',
          'notesGameplay2':'Notes #2 (gameplay)','size':'Size (Bytes)',
          'crc32':'CRC32','sha1':'SHA-1','sha256':'SHA-256'}
        def cell(row,field):
            idx=headers.get(col[field].lower())
            return as_text(row[idx]) if idx is not None else ''
        assert 'sha-256' in headers, (sheet_name,'Unexpected sheet header')
        gbuilds=collections.OrderedDict(); game_builds=[]
        for sheet_row,row in enumerate(rows[1:],2):
            if not any(as_text(x) for x in row): continue
            sha=cell(row,'sha256').lower(); sha1=cell(row,'sha1').lower()
            if not sha:
                filename=cell(row,'oldFilename') or cell(row,'sourceFilenames')
                if filename:
                    related_files.append({'game':slug,'collection':sheet_name,
                        'filename':filename,'notes':cell(row,'notesGeneral'),
                        'sheetRow':sheet_row,'type':'related non-JAR file'})
                continue
            if not HEX64.fullmatch(sha):
                errors.append(f'{sheet_name} row {sheet_row}: invalid SHA-256 {sha[:50]}'); continue
            if sha in hashes:
                errors.append(f'{sheet_name}!X{sheet_row}: duplicate SHA-256 {sha}'); continue
            if sha1 and not HEX40.fullmatch(sha1):
                errors.append(f'{sheet_name}!W{sheet_row}: invalid SHA-1 {sha1}'); continue
            hashes.add(sha)
            source=cell(row,'urls'); urls=list(dict.fromkeys(URL.findall(source)))
            size=cell(row,'size').replace(',','')
            if not size.isdigit() or int(size)<4:
                errors.append(f'{sheet_name}!U{sheet_row}: invalid byte size {size}'); continue
            values={field:cell(row,field) for field in FIELDS if field not in ('urls','size')}
            values.update(id=sha, sha256=sha, sha1=sha1, game=slug, collection=sheet_name,
                          urls=urls, size=int(size), sheetRow=sheet_row)
            if sheet_name=='Needs review':
                values['group']=f'NR-ROW{sheet_row:03d}' # Navigation key only; not a gameplay equivalence.
                values['unclassified']=True
            elif not values['group']:
                errors.append(f'{sheet_name}!A{sheet_row}: missing gameplay group'); continue
            game_builds.append(values); builds.append(values)
            if values['group']: gbuilds.setdefault(values['group'], []).append(values)
        for gid, records in gbuilds.items():
            def distinct(prop): return list(dict.fromkeys(r[prop] for r in records if r[prop]))
            notes=list(dict.fromkeys(n for r in records for n in
                           (r['notesGameplay'],r['notesGameplay2']) if n))
            groups.append({'id':gid,'game':slug,'collection':sheet_name,'title':title,'unclassified':sheet_name=='Needs review',
                           'buildIds':[r['id'] for r in records],'count':len(records),
                           'resolutions':distinct('resolution'),'languages':distinct('language'),
                           'devices':distinct('device'),'vendors':distinct('vendor'),
                           'notes':notes})
        games.append({'id':slug,'sheet':sheet_name,'title':title,'year':year,
                      'description':description,'count':len(game_builds),'groups':(0 if sheet_name=='Needs review' else len(gbuilds)),
                      'resolutions':len(set(r['resolution'] for r in game_builds if r['resolution'])),
                      'languages':len(set(r['language'] for r in game_builds if r['language'])),
                      'ungrouped': sheet_name=='Needs review'})
    if errors: raise ValueError('\n'.join(errors[:100]))
    result={'schemaVersion':3,'source':'PoP Java Games (2026 database)(1).xlsm',
            'notice':'Research classifications including experimental gameplay groups are reproduced from the supplied workbook. No JAR files are bundled.',
            'games':games, 'collections':[c[0] for c in COLLECTIONS],
            'stats':{'builds':len(builds),'groups':sum(not g['unclassified'] for g in groups),'games':len(games),
                     'resolutions':len(set(b['resolution'] for b in builds if b['resolution'])),
                     'languages':len(set(b['language'] for b in builds if b['language'])),
                     'linkedBuilds':sum(bool(b['urls']) for b in builds)},
            'groups':groups,'builds':builds,'relatedFiles':related_files}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n', encoding='utf-8')
    print(json.dumps({'relatedNonJars':len(related_files),'total':result['stats'],'games':[{'sheet':g['sheet'],'builds':g['count'],'groups':g['groups']} for g in games]},ensure_ascii=False,indent=2))
    return result

if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('workbook',type=Path); p.add_argument('output',type=Path); a=p.parse_args()
 convert(a.workbook,a.output)
