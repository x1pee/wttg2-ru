import json,struct
from pathlib import Path

TIPS={
 "Don't forget the flashlight.":'Не забудьте взять фонарик.',
 'Disconnecting from a network will prevent from being hacked / tracked by the police.':'Отключайтесь от сети, чтобы избежать взлома и слежки полиции.',
 'Different wifi networks will have better page load in times.':'В некоторых сетях Wi-Fi страницы загружаются быстрее.',
 'The game auto saves your progress every 15 mins.':'Игра автоматически сохраняет прогресс каждые 15 минут.',
 'Don’t forget about Bookmarks in A.N.N':'Не забывайте о закладках в A.N.N.',
 'Place your motion sensors where it makes the most sense.':'Размещайте датчики движения там, где они будут наиболее полезны.',
 'Pay attention to the time when web pages are down.':'Если страница недоступна, обратите внимание на время.',
 'Don’t peek too much.':'Не выглядывайте слишком часто.',
}

def read(raw):
    # This Unity 2017 class has a string[] which the generator incorrectly
    # describes as one string. Decode the actual aligned array explicitly.
    marker=next(iter(TIPS)).encode();start=raw.find(marker)-8
    if start<0:raise ValueError('Loading tips array not found')
    count=struct.unpack_from('<i',raw,start)[0]
    if count!=len(TIPS):raise ValueError('Unexpected loading tip count')
    at=start+4;values=[]
    for _ in range(count):
        size=struct.unpack_from('<i',raw,at)[0];at+=4
        values.append(raw[at:at+size].decode('utf-8'));at=(at+size+3)//4*4
    if set(values)!=set(TIPS) or at!=len(raw):raise ValueError('Unexpected loading tips data')
    return start,values

def patch(obj):
    raw=obj.get_raw_data();start,values=read(raw)
    out=bytearray(raw[:start])+struct.pack('<i',len(values))
    for value in values:
        data=TIPS[value].encode('utf-8');out+=struct.pack('<i',len(data))+data
        out+=b'\0'*((-len(out))%4)
    obj.set_raw_data(bytes(out))
    return [{'en':value,'ru':TIPS[value]} for value in values]

def update_dictionary():
    path=Path(__file__).parent/'translations.json'
    values=json.loads(path.read_text('utf-8'));values.update(TIPS)
    path.write_text(json.dumps(values,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':
    import inspect_game as ig
    original=ig.ROOT.parent/'WTTG2_RU_Backup/WTTG2_Data/level2'
    env=ig.UnityPy.load(str(original));rows=read(env.file.objects[89].get_raw_data())[1]
    print(json.dumps(rows,ensure_ascii=False,indent=2))
    env=ig.UnityPy.load(str(ig.OUT/'stage/level2'))
    changes=patch(env.file.objects[89]);(ig.OUT/'stage/level2').write_bytes(env.file.save())
    update_dictionary()
    (ig.OUT/'loading-tip-translations.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Translated loading tips:',len(changes))
