import json,re,hashlib,struct,sys
from pathlib import Path
from html.parser import HTMLParser
import inspect_game as ig
import numpy as np
from inspect_game import OUT,UnityPy,TypeTreeGenerator
GAME=Path(r'W:\Games\Welcome to the Game II')
DATA=Path(sys.argv[1]) if len(sys.argv)>1 else GAME/'WTTG2_Data'
BACKUP=GAME/'WTTG2_RU_Backup/WTTG2_Data'
ig.ROOT=BACKUP;old=ig.read_pack();ig.ROOT=DATA;new=ig.read_pack()
checks=[]
def check(condition,label):
    assert condition,label;checks.append(label)
for name,data in old.items():
    if name.endswith('.css'):
        original=data.decode('utf-8-sig');expected=re.sub(r"'(?:(?:OCR A Std)|Hobo|Cooper Std Black)'",'"Cascadia Code",WTTG2RU',original)
        check(new[name].decode('utf-8-sig')==expected,'Only font fallback changed '+name)
    elif not name.endswith('.html'):check(new[name]==data,'Unchanged resource '+name)
    else:
        a=data.decode('utf-8-sig');b=new[name].decode('utf-8-sig')
        check(re.findall(r'<script\b[^>]*>.*?</script>',a,re.S|re.I)==re.findall(r'<script\b[^>]*>.*?</script>',b,re.S|re.I),'Scripts preserved '+name)
        attrs=r'\b(?:id|class|href|src|onclick|onmouseover|onmouseout|name)\s*=\s*([\"\'])(.*?)\1'
        before=re.findall(attrs,a,re.I|re.S);after=re.findall(attrs,b,re.I|re.S)
        after=[x for x in after if x[1]!='wttg2-ru-font']
        check(before==after,'IDs, links, callbacks preserved '+name)
        pattern=r'[A-Za-z0-9+/]{28,}'
        check(re.findall(pattern,a)==re.findall(pattern,b),'Long codes preserved '+name)
g=TypeTreeGenerator('2017.3.0f3')
for dll in (GAME/'WTTG2_Data/Managed').glob('*.dll'):
    original=BACKUP/'Managed'/dll.name
    g.load_dll((original if original.exists() else dll).read_bytes())
for path in (OUT/'stage').glob('*.assets'):
    env=UnityPy.load(str(DATA/path.name));env.path=str(DATA);env.typetree_generator=g
    for o in env.objects:
        if o.type.name=='MonoBehaviour':
            cls=o.parse_monobehaviour_head().m_Script.deref_parse_as_object().m_ClassName
            if cls=='TMP_FontAsset':
                tree=o.read_typetree(nodes=o.generate_monobehaviour_node());ids={x['id'] for x in tree['m_glyphInfoList']}
                check(set(range(0x410,0x450)).issubset(ids),'TMP Cyrillic '+path.name+' '+tree['m_Name'])
                check({0x401,0x451}.issubset(ids),'TMP Yo '+path.name+' '+tree['m_Name'])
                texture=env.file.objects[tree['atlas']['m_PathID']].read();pixels=np.array(texture.image)
                for x in tree['m_glyphInfoList']:
                    check(x['x']>=0 and x['y']>=0 and x['x']+x['width']<=tree['m_fontInfo']['AtlasWidth'] and x['y']+x['height']<=tree['m_fontInfo']['AtlasHeight'],'Glyph bounds '+path.name+' '+str(x['id']))
                    if x['id']!=32:
                        tile=pixels[int(x['y']):int(x['y']+x['height']),int(x['x']):int(x['x']+x['width'])]
                        check(tile.max()>127,'Glyph ink at TMP 2017 top-origin coordinates '+path.name+' '+str(x['id']))
(OUT/'structural-qa.json').write_text(json.dumps({'passed':len(checks),'checks':checks},ensure_ascii=False,indent=2),encoding='utf-8')
print('Passed',len(checks),'structural checks')
