import sys, json, struct, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent/'deps'))
import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
ROOT=Path(r'W:\Games\Welcome to the Game II\WTTG2_Data')
OUT=Path(__file__).parent
def read_pack(path=None):
    with (Path(path) if path is not None else ROOT/'Resources/browser_assets').open('rb') as f:
        def string():
            n=0; shift=0
            while True:
                b=f.read(1)[0]; n|=(b&127)<<shift
                if b<128:break
                shift+=7
            return f.read(n).decode('utf-8')
        assert string()=='zfbRes_v1'
        entries=[]
        for _ in range(struct.unpack('<i',f.read(4))[0]):
            name=string(); offset,size=struct.unpack('<qi',f.read(12));entries.append((name,offset,size))
        result={}
        for name,offset,size in entries:
            f.seek(offset); result[name]=f.read(size)
        return result
if __name__=='__main__':
    pack=read_pack(); (OUT/'browser-source').mkdir(exist_ok=True)
    for name,data in pack.items():
        if name.endswith(('.html','.js','.css')):
            dest=OUT/'browser-source'/name.lstrip('/');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    rows=[];fonts=[];counts=collections.Counter()
    files=[p for p in ROOT.iterdir() if p.name.endswith('.assets') or (p.name.startswith('level') and p.name[5:].isdigit())]
    generator=TypeTreeGenerator('2017.3.0f3')
    generator.load_local_dll_folder(str(ROOT/'Managed'))
    errors=collections.Counter()
    for p in files:
        print('Reading',p.name,flush=True)
        env=UnityPy.load(str(p))
        env.typetree_generator=generator
        for obj in env.objects:
            counts[obj.type.name]+=1
            if obj.type.name in ('MonoBehaviour','TextAsset','Font'):
                try:
                    node=obj.generate_monobehaviour_node() if obj.type.name=='MonoBehaviour' else None
                    tree=obj.read_typetree(nodes=node)
                except Exception as e:errors[str(e)[:100]]+=1;continue
                if obj.type.name=='Font':
                    fonts.append({'file':p.name,'id':obj.path_id,'tree':tree})
                def walk(value,path):
                    if isinstance(value,dict):
                        for k,v in value.items():walk(v,path+[k])
                    elif isinstance(value,list):
                        for i,v in enumerate(value):walk(v,path+[i])
                    elif isinstance(value,str) and value and path[-1] not in ('m_Name','m_EditorClassIdentifier'):
                        rows.append({'file':p.name,'id':obj.path_id,'name':tree.get('m_Name',''),'class':obj.parse_monobehaviour_head().m_Script.deref_parse_as_object().m_ClassName if obj.type.name=='MonoBehaviour' else obj.type.name,'path':path,'text':value})
                walk(tree,[])
    (OUT/'asset-strings.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'fonts.json').write_text(json.dumps(fonts,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    print('COUNTS',counts,'strings',len(rows),'fonts',len(fonts),'errors',errors)
