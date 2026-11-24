#!/usr/bin/env python3
"""Convert the author-supplied PoP XLSM research catalogue to static website JSON.

Uses openpyxl; no Excel macros, JAR files, or binaries are embedded.
"""
import argparse, collections, json, re
from pathlib import Path
from openpyxl import load_workbook

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
FPS_NOTE = re.compile(r'\blimit\s+fps\s+to\s+(15|30|60)\b', re.IGNORECASE)
UNPLAYABLE_NOTE = re.compile(r'\bunplayable\b', re.IGNORECASE)
HAREM_FAMILY = re.compile(r'^(HA-G[0-9]{2})(?:-([a-z]+))?$', re.IGNORECASE)
SOT_FAMILY = re.compile(r'^(SoT-G0[12])(?:-([a-z]+))?$', re.IGNORECASE)
WW_FAMILY = re.compile(r'^(WW-G0[12])(?:-([a-z]+))?$', re.IGNORECASE)
HAREM_PREVIEWS = {
    'HA-G01': 'assets/previews/harem-g01.png',
    'HA-G02': 'assets/previews/harem-g02.png',
    'HA-G03': 'assets/previews/harem-g03.png',
}
SOT_PREVIEWS = {
    'SoT-G01': 'assets/previews/sot-g01.png',
    'SoT-G02': 'assets/previews/sot-g02.png',
}
WW_PREVIEWS = {
    'WW-G01': 'assets/previews/ww-g01.png',
    'WW-G02': 'assets/previews/ww-g02.png',
}
# Only these collections have reviewed gameplay families and preview images.
# Letter-suffixed group IDs remain independent research subgroup IDs.
FAMILY_CONFIG = {
    'Harem Adventures': (HAREM_FAMILY, 'HA-G', HAREM_PREVIEWS),
    'SoT': (SOT_FAMILY, 'SoT-G', SOT_PREVIEWS),
    'WW': (WW_FAMILY, 'WW-G', WW_PREVIEWS),
}

# Manufacturer names explicitly supported by the bundled FreeJ2ME phone menu.
# Unsupported brands are recognized to avoid choosing a profile for mixed lists.
PHONE_TYPES = {
    'Nokia': r'\bnokia\b',
    'Siemens': r'\bsiemens\b',
    'Motorola': r'\bmotorola\b',
    'SonyEricsson': r'\bsony[\s-]*ericsson\b',
}
OTHER_MANUFACTURERS = re.compile(
    r'\b(?:samsung|lg|alcatel|sagem|sharp|panasonic|philips|nec|benq|'
    r'blackberry|htc|huawei|zte|sanyo|toshiba|kyocera|pantech|'
    r'vodafone|fujitsu|mitsubishi|ericsson|sony)\b', re.IGNORECASE)


def classify_device(device):
    """Infer a single supported manufacturer, not a particular phone model."""
    text = device or ''
    matches = [name for name, pattern in PHONE_TYPES.items()
               if re.search(pattern, text, re.IGNORECASE)]
    # Remove recognized brands before checking unsupported names, so Sony
    # Ericsson is not mistaken for separate Sony and Ericsson manufacturers.
    for pattern in PHONE_TYPES.values():
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    if len(matches) == 1 and not OTHER_MANUFACTURERS.search(text):
        return matches[0]
    return None


def classify_notes(notes):
    """Extract playback hints from all three free-text Notes fields."""
    joined = '\n'.join(n for n in notes if n)
    limits = {int(m) for m in FPS_NOTE.findall(joined)}
    if len(limits) > 1:
        raise ValueError('conflicting FPS limits: ' + ', '.join(map(str, sorted(limits))))
    return bool(UNPLAYABLE_NOTE.search(joined)), (next(iter(limits)) if limits else None)


def as_text(value):
    return '' if value is None else str(value).strip()

def convert(input_path, output):
    w=load_workbook(input_path, read_only=True, data_only=True)
    games=[]; builds=[]; groups=[]; families=[]; related_files=[]; hashes=set(); errors=[]
    for sheet_name,slug,title,year,description in COLLECTIONS:
        s=w[sheet_name]
        rows=s.iter_rows(values_only=True)
        headers={as_text(v).lower():i for i,v in enumerate(next(rows)) if v}
        # Gameplay Group is a column name, not a fixed label.  For example,
        # both 'Gameplay Group' and 'Gameplay Group (experimental)' are valid.
        group_headers=[name for name in headers if name.startswith('gameplay group')]
        if sheet_name != 'Needs review':
            if not group_headers:
                raise ValueError(f'{sheet_name}: missing column whose header starts with Gameplay Group')
            if len(group_headers) > 1:
                raise ValueError(f'{sheet_name}: ambiguous Gameplay Group columns: {group_headers}')
        col={
          'group':group_headers[0] if group_headers else 'Gameplay Group', 'name':'Applet Name', 'displayTitle':'Title Screen Name',
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
            return as_text(row[idx]) if idx is not None and idx < len(row) else ''
        assert 'sha-256' in headers, (sheet_name,'Unexpected sheet header')
        gbuilds=collections.OrderedDict(); game_builds=[]
        for sheet_row,row in enumerate(rows,2):
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
            # Excel may return whole byte counts as floats (e.g. 89208.0).
            if re.fullmatch(r'[0-9]+(?:\.0+)?', size):
                size=size.split('.',1)[0]
            if not re.fullmatch(r'[0-9]+', size) or int(size)<4:
                errors.append(f'{sheet_name}!U{sheet_row}: invalid byte size {size}'); continue
            values={field:cell(row,field) for field in FIELDS if field not in ('urls','size')}
            values.update(id=sha, sha256=sha, sha1=sha1, game=slug, collection=sheet_name,
                          urls=urls, size=int(size), sheetRow=sheet_row)
            if sheet_name=='Needs review':
                values['group']=f'NR-ROW{sheet_row:03d}' # Navigation key only; not a gameplay equivalence.
                values['unclassified']=True
            elif not values['group']:
                errors.append(f'{sheet_name}!A{sheet_row}: missing gameplay group'); continue
            values['phoneType'] = classify_device(values['device'])
            # These are independent build-level flags, never inherited from a group.
            notes = [values[k] for k in ('notesGeneral', 'notesGameplay', 'notesGameplay2')]
            try:
                values['unplayable'], values['fpsLimit'] = classify_notes(notes)
            except ValueError as error:
                errors.append(f'{sheet_name} row {sheet_row}: {error}'); continue
            if sheet_name in FAMILY_CONFIG:
                pattern, prefix, _previews = FAMILY_CONFIG[sheet_name]
                match = pattern.fullmatch(values['group'])
                if not match:
                    errors.append(f'{sheet_name}!A{sheet_row}: unrecognized gameplay family {values["group"]!r}'); continue
                values['family'] = prefix + match.group(1)[-2:]
                values['variant'] = (match.group(2) or '').lower()
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
        if sheet_name in FAMILY_CONFIG:
            previews = FAMILY_CONFIG[sheet_name][2]
            for fid in dict.fromkeys(b['family'] for b in game_builds):
                preview = previews.get(fid, '')
                members = [b for b in game_builds if b.get('family') == fid]
                if members:
                    families.append({'id':fid, 'game':slug, 'image':preview,
                                     'buildIds':[b['sha256'] for b in members],
                                     'count':len(members)})
        games.append({'id':slug,'sheet':sheet_name,'title':title,'year':year,
                      'description':description,'count':len(game_builds),'groups':(0 if sheet_name=='Needs review' else len(gbuilds)),
                      'resolutions':len(set(r['resolution'] for r in game_builds if r['resolution'])),
                      'languages':len(set(r['language'] for r in game_builds if r['language'])),
                      'ungrouped': sheet_name=='Needs review'})
    w.close()
    if errors: raise ValueError('\n'.join(errors[:100]))
    result={'schemaVersion':3,'source':input_path.name,
            'notice':'Research classifications including experimental gameplay groups are reproduced from the supplied workbook. No JAR files are bundled.',
            'games':games, 'collections':[c[0] for c in COLLECTIONS],
            'stats':{'builds':len(builds),'groups':sum(not g['unclassified'] for g in groups),'games':len(games),
                     'resolutions':len(set(b['resolution'] for b in builds if b['resolution'])),
                     'languages':len(set(b['language'] for b in builds if b['language'])),
                     'linkedBuilds':sum(bool(b['urls']) for b in builds)},
            'groups':groups,'families':families,'builds':builds,'relatedFiles':related_files}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n', encoding='utf-8')
    print(json.dumps({'relatedNonJars':len(related_files),'total':result['stats'],'games':[{'sheet':g['sheet'],'builds':g['count'],'groups':g['groups']} for g in games]},ensure_ascii=False,indent=2))
    return result

if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('workbook',type=Path); p.add_argument('output',type=Path); a=p.parse_args()
 convert(a.workbook,a.output)
