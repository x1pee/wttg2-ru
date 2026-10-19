import json,struct,hashlib,collections,re,html,copy
from pathlib import Path
from inspect_game import ROOT,OUT,UnityPy,TypeTreeGenerator,read_pack
from PIL import Image,ImageDraw,ImageFont
from translate_game import cache,tr,tr_html,SAFE_FIELDS,EXCLUDED_DIRS,unsafe_text
from font_patch import covers_ru,replace_dynamic_font,make_sdf_font
from release_config import original_path

STAGE=OUT/'stage';STAGE.mkdir(exist_ok=True)
def write_string(t):
    raw=t.encode('utf-8');n=len(raw);prefix=bytearray()
    while n>=128:prefix.append((n&127)|128);n>>=7
    prefix.append(n);return bytes(prefix)+raw
def build_pack():
    entries=read_pack(original_path('Resources/browser_assets'));changed=[];excluded=[]
    for name,data in list(entries.items()):
        if name.endswith('.css'):
            text=data.decode('utf-8-sig');revised=re.sub(r"'(?:(?:OCR A Std)|Hobo|Cooper Std Black)'",'"Cascadia Code",WTTG2RU',text)
            if revised!=text:entries[name]=revised.encode('utf-8')
        if name.endswith('.html'):
            text=data.decode('utf-8-sig')
            if name.split('/')[1].lower() in EXCLUDED_DIRS:excluded.append(name);continue
            if unsafe_text(text):excluded.append(name)
            new=tr_html(text,name)
            # Preserve the original family; Cascadia supplies missing Cyrillic glyphs.
            new=re.sub(r"'(?:(?:OCR A Std)|Hobo|Cooper Std Black)'",'"Cascadia Code",WTTG2RU',new)
            folder=name.rsplit('/',1)[0]+'/'
            has_font='font-family' in text or any(b'font-family' in value for key,value in entries.items() if key.startswith(folder) and key.endswith('.css'))
            css='<style id="wttg2-ru-font">@font-face{font-family:WTTG2RU;src:url("localGame://ru-font/CascadiaCode.ttf")}'+('' if has_font else 'body{font-family:"Cascadia Code",WTTG2RU,monospace}')+'</style>'
            new=new.replace('</head>',css+'</head>')
            if new!=text:entries[name]=new.encode('utf-8');changed.append(name)
    from font_patch import FONT_BYTES
    entries['/ru-font/CascadiaCode.ttf']=FONT_BYTES
    header=write_string('zfbRes_v1')+struct.pack('<i',len(entries))
    offset=len(header)+sum(len(write_string(name))+12 for name in entries)
    index=bytearray(header);payload=[]
    for name,data in entries.items():
        index.extend(write_string(name));index.extend(struct.pack('<qi',offset,len(data)));payload.append(data);offset+=len(data)
    target=STAGE/'Resources/browser_assets';target.parent.mkdir(exist_ok=True);target.write_bytes(bytes(index)+b''.join(payload))
    return {'pages':changed,'excluded':excluded,'entries':len(entries)}

def build_assets():
    generator=TypeTreeGenerator('2017.3.0f3')
    for dll in (ROOT/'Managed').glob('*.dll'):
        if dll.name!='WTTG2RU.dll':generator.load_dll(original_path('Managed/'+dll.name).read_bytes())
    counts=collections.Counter();report=[];fontreport=[];failures=[]
    characters={ord(c) for value in cache.values() for c in value if not c.isspace()}
    files=[p for p in ROOT.iterdir() if p.name.endswith('.assets') or (p.name.startswith('level') and p.name[5:].isdigit())]
    for path in files:
        path=original_path(path.name)
        env=UnityPy.load(str(path));env.path=str(ROOT);env.typetree_generator=generator;modified=False
        for obj in env.objects:
            if obj.type.name=='TextAsset':
                tree=obj.read_typetree()
                from browser_templates import patch
                old=tree['m_Script'];new=patch(tree['m_Name'],old)
                if new!=old:
                    tree['m_Script']=new;obj.save_typetree(tree);modified=True;counts['BrowserTemplates']+=1
                continue
            if obj.type.name=='Texture2D' and path.name=='sharedassets3.assets':
                texture=obj.read()
                captions={'notesTitle':'Заметки','incomingCallTextLarge':'ВХОДЯЩИЙ ЗВОНОК','adamTextSmall':'Адам','adamTextLarge':'Адам','gameOver':'КОНЕЦ ИГРЫ'}
                if texture.m_Name in captions:
                    from font_patch import CASCADIA
                    text=captions[texture.m_Name];w,h=texture.m_Width,texture.m_Height
                    size=h-2
                    while size>5:
                        font=ImageFont.truetype(str(CASCADIA),size)
                        if font.getlength(text)<=w-(16 if texture.m_Name=='gameOver' else 2):break
                        size-=1
                    image=Image.new('RGBA',(w,h));left,top,right,bottom=font.getbbox(text)
                    ImageDraw.Draw(image).text(((w-(right-left))/2-left,(h-(bottom-top))/2-top),text,font=font,fill=(0,210,35,255) if texture.m_Name=='gameOver' else 'white')
                    if texture.m_Name=='gameOver':
                        from PIL import ImageFilter
                        image=Image.alpha_composite(image.filter(ImageFilter.GaussianBlur(4)),image)
                    texture.image=image;texture.save();modified=True;counts['TextureCaptions']+=1
                continue
            if obj.type.name=='Font':
                tree=obj.read_typetree()
                bitmap_cyrillic=set(range(0x410,0x450)).issubset({x['index'] for x in tree['m_CharacterRects']})
                if not covers_ru(tree['m_FontData']) and not bitmap_cyrillic:
                    replace_dynamic_font(tree);obj.save_typetree(tree);modified=True
                    fontreport.append({'file':path.name,'id':obj.path_id,'name':tree['m_Name'],'change':'Cascadia Code'})
                continue
            if obj.type.name!='MonoBehaviour':continue
            try:
                cls=obj.parse_monobehaviour_head().m_Script.deref_parse_as_object().m_ClassName
                if cls=='LoadingScreenManager':
                    from loading_tips import patch
                    tips=patch(obj);counts['LoadingTips']+=len(tips);modified=True
                    report.extend(dict(file=path.name,id=obj.path_id,field='tips',**tip) for tip in tips)
                    continue
                if cls not in SAFE_FIELDS and cls not in ('WebPageDefinition','TMP_FontAsset'):continue
                node=obj.generate_monobehaviour_node();tree=obj.read_typetree(nodes=node)
            except Exception as exc:failures.append({'file':path.name,'id':obj.path_id,'error':str(exc)});continue
            obj_changed=False
            if cls=='TMP_FontAsset':
                ids={g['id'] for g in tree['m_glyphInfoList']}
                if not set(range(0x410,0x450)).issubset(ids):
                    image=make_sdf_font(tree,characters)
                    ref=tree['atlas'];assert ref['m_FileID']==0
                    texture=env.file.objects[ref['m_PathID']].read();rgba=__import__('PIL.Image',fromlist=['Image']).new('RGBA',image.size,(255,255,255,255));rgba.putalpha(image);texture.image=rgba;texture.save()
                    mat=env.file.objects[tree['material']['m_PathID']].read_typetree()
                    mat['m_SavedProperties']['m_Floats']=[(key,float(image.width) if key=='_TextureWidth' else float(image.height) if key=='_TextureHeight' else value) for key,value in mat['m_SavedProperties']['m_Floats']]
                    env.file.objects[tree['material']['m_PathID']].save_typetree(mat)
                    obj_changed=True;fontreport.append({'file':path.name,'id':obj.path_id,'name':tree['m_Name'],'change':'Cascadia Code SDF','glyphs':len(tree['m_glyphInfoList'])})
            else:
                for field in SAFE_FIELDS.get(cls,set()):
                    if (cls=='WebSiteDefinition' and field=='PageTitle') or (cls=='WebPageDefinition' and field=='PageName'):continue
                    if field not in tree or not isinstance(tree[field],str):continue
                    old=tree[field];new=tr(old)
                    if new!=old:
                        tree[field]=new;obj_changed=True;counts[cls]+=1
                        report.append({'file':path.name,'id':obj.path_id,'field':field,'en':old,'ru':new})
                        if cls=='TextMeshProUGUI':
                            tree['m_enableAutoSizing']=True
                            tree['m_fontSizeMin']=min(tree['m_fontSizeMin'],tree['m_fontSize']*.5)
                            if len(new)<32:
                                tree['m_enableWordWrapping']=False
                                tree['m_fontSizeMin']=min(tree['m_fontSizeMin'],8.0)
                        elif cls=='Text':
                            fontdata=tree['m_FontData'];fontdata['m_BestFit']=True
                            if path.name=='sharedassets3.assets' and fontdata['m_Font']['m_FileID']==0 and fontdata['m_Font']['m_PathID']==425:fontdata['m_BestFit']=False
                            fontdata['m_MinSize']=max(8,min(fontdata['m_MinSize'],int(fontdata['m_FontSize']*.65)))
                            fontdata['m_MaxSize']=fontdata['m_FontSize']
                if cls=='WebPageDefinition' and tree.get('PageHTML'):
                    old=tree['PageHTML']
                    # Alternate saved copies of these excluded pages contain
                    # different demo keys than their browser-pack equivalents.
                    excluded_copy=path.name=='sharedassets3.assets' and obj.path_id in {1636,1638,1639,1640,1641,1642,1721}
                    new=old if excluded_copy else tr_html(old)
                    if new!=old:tree['PageHTML']=new;obj_changed=True;counts['EmbeddedHTML']+=1
            if obj_changed:
                obj.save_typetree(tree,nodes=node);modified=True
        if modified:
            if path.name=='level1':
                from layout_patch import patch_title_layout
                patch_title_layout(env,counts)
            target=STAGE/path.name;target.write_bytes(env.file.save());print('Built',path.name,target.stat().st_size,flush=True)
    return {'counts':dict(counts),'fields':report,'fonts':fontreport,'failures':failures}

if __name__=='__main__':
    report={'browser':build_pack(),'assets':build_assets()}
    (OUT/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('BUILT',report['assets']['counts'],'fonts',len(report['assets']['fonts']),'errors',report['assets']['failures'])
