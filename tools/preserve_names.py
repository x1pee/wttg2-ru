import json,re
from pathlib import Path
OUT=Path(__file__).parent
rows=json.loads((OUT/'asset-strings.json').read_text('utf-8'))
names={x['text'] for x in rows if x['class']=='WebSiteDefinition' and x['path']==['PageTitle']}
names.update({'Bug Chaser','BugChaser','Heirloom','EvilCollection','TheGrey','TheLightWithin',
 'TheBlackWaves','TheEndForNY','WeRock','MortalMasks','MortalMasked','MyGut','MilkSupply',
 'Shadow Market','zeroDay Market','Noir Tunnel','NOIRTUNNEL','Blue Whisper','LOLPY DISC',
 'Key Cue','Motion Alert','Backdoor Hack','A.N.N','skyBREAK','zeroDay','ZONEWALL',
 'ZoneWall','memD3FR4G3R','stackPUSHER','N0D3H3X3R','Breather','Noir',
 'DOS Coin','DOS Coins','DOScoin','DOScoins','Bitcoin','BTC','PGP'})
def normalized(value):return re.sub(r'[^a-z0-9]','',value.lower())
canonical={normalized(name) for name in names}
def preserve(value):
    stripped=value.strip()
    return normalized(stripped) in canonical or bool(re.fullmatch(r'[\d.,]+\s+DOS\s?coins?',stripped,re.I)) or stripped.startswith('-----') or stripped.startswith('Version: BCPG')
replacements={
 'Теневой рынок':'Shadow Market','Теневого рынка':'Shadow Market','Теневом рынке':'Shadow Market',
 'Теневому рынку':'Shadow Market','теневой рынок':'Shadow Market','теневого рынка':'Shadow Market',
 'теневом рынке':'Shadow Market','теневому рынку':'Shadow Market',
 'Нуар':'Noir','НУАР':'Noir','Дышащий':'Breather','Дышащего':'Breather',
 'Дышащему':'Breather','дышащий':'Breather','дышащего':'Breather',
 'Кукольника':'Doll Maker','Кукольнику':'Doll Maker','Кукольник':'Doll Maker',
 'кукольника':'Doll Maker','кукольнику':'Doll Maker','кукольник':'Doll Maker',
}
def restore_terms(value):
    for old,new in replacements.items():value=value.replace(old,new)
    return re.sub(r'(?i)битко[ий]н[а-яё]*','Bitcoin',value)
if __name__=='__main__':
    cache_path=OUT/'translations.json';cache=json.loads(cache_path.read_text('utf-8'));count=0
    cache.update({'empty':'пусто','share':'делиться','rest':'остальное','collecting':'сбор',
     'thick':'густой','ENTER':'ВВОД','SEE':'СМОТРИ','man':'человек','swallow':'поглотят',
     'advances':'приближение','Dacite':'Дацит','Trachyte':'Трахит','pyramids':'пирамиды',
     'drilling':'бурение','dying':'угасающее','keep':'сохранить',"earth's":'Земли',
     'population':'населения','unloading':'выгрузка','WASTE':'ТРАТЬ','committing':'совершая',
     'content':'материалы','MEDIA':'МАТЕРИАЛЫ','leaked':'попавшие в сеть',
     'COMPANION':'СПУТНИК','RETURN':'ВЕРНУТЬСЯ','bleaching':'отбеливающем',
     'MAKE':'СДЕЛАТЬ','LOADING':'ЗАГРУЗКА','BETWEEN':'МЕЖДУ','truly grey.':'по-настоящему серым.'})
    for en,ru in list(cache.items()):
        new=en if preserve(en) else restore_terms(ru)
        if new!=ru:count+=1;cache[en]=new
    cache_path.write_text(json.dumps(cache,ensure_ascii=False,indent=2),encoding='utf-8')
    paragraph_path=OUT/'paragraph-edits.json';paragraphs=json.loads(paragraph_path.read_text('utf-8'))
    paragraphs={en:restore_terms(ru) for en,ru in paragraphs.items()}
    paragraph_path.write_text(json.dumps(paragraphs,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'proper-names.json').write_text(json.dumps(sorted(names),ensure_ascii=False,indent=2),encoding='utf-8')
    import base64
    subtitle_path=OUT/'stage/RU/subtitles.tsv'
    subtitle_rows=[]
    for line in subtitle_path.read_text('utf-8').splitlines():
        fields=line.split('\t');ru=base64.b64decode(fields[3]).decode('utf-8')
        fields[3]=base64.b64encode(restore_terms(ru).encode()).decode();subtitle_rows.append('\t'.join(fields))
    subtitle_path.write_text('\n'.join(subtitle_rows),encoding='utf-8')
    print('Proper names and currencies restored:',count)
