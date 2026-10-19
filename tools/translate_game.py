import sys,json,re,html,time,urllib.request,urllib.parse,concurrent.futures,threading
from pathlib import Path
from html.parser import HTMLParser
from inspect_game import ROOT,OUT,read_pack

MANUAL={
'CONTINUE':'ПРОДОЛЖИТЬ','YES':'ДА','NO':'НЕТ','ON':'ВКЛ','OFF':'ВЫКЛ','QUIT':'ВЫХОД','OPTIONS':'НАСТРОЙКИ','QUALITY:':'КАЧЕСТВО:','BACK':'НАЗАД','APPLY':'ПРИМЕНИТЬ','MIC:':'МИКРОФОН:','RESOLUTION:':'РАЗРЕШЕНИЕ:','NEW GAME':'НОВАЯ ИГРА','V-SYNC:':'V-SYNC:','WINDOW MODE:':'ОКОННЫЙ РЕЖИМ:','NUDITY:':'НАГОТА:',
'Very High':'Очень высокое','High':'Высокое','Medium':'Среднее','Low':'Низкое','Very Low':'Очень низкое',
'(will make elements of the game more difficult)':'(некоторые элементы игры станут сложнее)',
'Starting a new game will overwrite your current progress.':'Новая игра заменит ваш текущий прогресс.','Are you sure?':'Вы уверены?',
'QUIT GAME':'ВЫЙТИ ИЗ ИГРЫ','PAUSED':'ПАУЗА','EXIT TO MAIN MENU':'ГЛАВНОЕ МЕНЮ','Mouse Sensitivity':'Чувствительность мыши','NOTES: KEPT':'ЗАМЕТКИ СОХРАНЕНЫ',
'Network Manager':'Сетевые подключения','Source Viewer':'Исходный код','Shadow Market':'Теневой рынок','zeroDay Market':'Магазин zeroDay','Notes':'Заметки','NOTES':'ЗАМЕТКИ','Police':'Полиция','Breather':'Дышащий','Lucas':'Лукас','Noir':'Нуар','Noir Tunnel':'Туннель Нуар','Clint Edwards':'Клинт Эдвардс',
'CAST YOUR VOTES!':'ГОЛОСУЙТЕ!','Cancel':'Отмена','Password:':'Пароль:','No Remote VPNs Active':'Нет активных удалённых VPN','You must be connected to the internet to use the Shadow Market':'Для доступа к Теневому рынку подключитесь к интернету','You must be connected to the internet to use the zeroDay Market':'Для доступа к магазину zeroDay подключитесь к интернету',
'Enter note...':'Введите заметку...','Disconnect...':'Отключиться...','Connect':'Подключиться','Master Key...':'Главный ключ...','NAME':'ИМЯ','AGE':'ВОЗРАСТ','UNIT':'КВАРТИРА','UNLOCK':'РАЗБЛОКИРОВАТЬ',
'Powering Off':'Выключение','Powering On':'Включение',"No VPN'S Activated":'Нет активных VPN','No Motion Sensors Active':'Нет активных датчиков движения','Offline...':'Нет подключения...','Please Wait...':'Подождите...',
'GAINED: 4.268':'ПОЛУЧЕНО: 4.268','LOST: 4.268':'ПОТЕРЯНО: 4.268','BUY':'КУПИТЬ','OWNED':'КУПЛЕНО','SHIPPED!':'ОТПРАВЛЕНО!','Shipping...':'Доставка...','Installing...':'Установка...','Stock: 1':'В наличии: 1','Stock:':'В наличии:',
'Bath Room':'Ванная','Dead Drop':'Тайник','Lobby Floor Hallway':'Коридор первого этажа','Maintenace Room':'Подсобка','Main Room':'Гостиная','Outside':'Улица','Stairway':'Лестница','Lobby':'Вестибюль','Unknown':'Неизвестно','None':'Нет',
'YOU WERE KILLED':'ВАС УБИЛИ','YOU DISAPPOINTED THE DOLL MAKER':'ВЫ РАЗОЧАРОВАЛИ КУКОЛЬНИКА','TIMES UP!':'ВРЕМЯ ВЫШЛО!','Pro Tip:':'Совет:',
'Motion Sensor':'Датчик движения','Police Scanner':'Полицейский сканер','Remote VPN':'Удалённый VPN','Blue Whisper':'Blue Whisper','LOLPY DISC':'LOLPY DISC','Key Cue':'Индикатор ключа','Motion Alert':'Сигнал движения','Backdoor Hack':'Бэкдор',
'Initializing...':'Инициализация...','Scanning...':'Сканирование...','Locating...':'Поиск местоположения...','Location Found!':'Местоположение найдено!','Incoming Message...':'Входящее сообщение...',
'Master Key':'Главный ключ','Transient Key':'Временный ключ','Scanned WEP Network Results':'Результаты поиска сетей WEP','Scanned WPA Network Results':'Результаты поиска сетей WPA','Scanned WPA2 Network Results':'Результаты поиска сетей WPA2',
'The WiFi network':'Сеть Wi-Fi','You have the following crackers installed:':'У вас установлены следующие модули взлома:','You do not have the WPA cracker installed!':'У вас не установлен модуль взлома WPA!','You do not have the WPA2 cracker installed!':'У вас не установлен модуль взлома WPA2!',
'Invalid port number. Valid port range is 1 - 1000.':'Неверный номер порта. Допустимый диапазон: 1–1000.','Invalid channel number.':'Неверный номер канала.','Invalid port number.':'Неверный номер порта.','Invalid injection amount.':'Неверное число запросов.','Invalid injection amount. Please select 1 - 1000':'Неверное число запросов. Укажите число от 1 до 1000.',
'Too many injection requests were sent at once. Network is now offline.':'Отправлено слишком много запросов одновременно. Сеть отключилась.','Remember to only send a little at a time to prevent the system from going offline.':'Отправляйте запросы небольшими порциями, чтобы сеть не отключилась.','Injection De-Auth injection was successful! Network is now ready to crack.':'Запрос деаутентификации выполнен! Теперь сеть можно взломать.',
'That Sounds good. I choose that.':'Звучит хорошо. Я выбираю это.','What are you looking for in return?':'Что ты хочешь взамен?','I want to live...':'Я хочу жить...',"I will take Amalea's place..":'Я займу место Амалии...', 'Adam?':'Адам?','Where is Amalea?':'Где Амалия?','What the fuck are you talking about?':'Какого хрена ты несёшь?','Survival of what?':'Выжить в чём?','You’re sick!':'Ты больной!','I’m flattered...':'Я польщён...','Was? Is she dead?':'Была? Она мертва?','Answer to what?':'Ответ на что?','Poetic':'Поэтично','What do you want!?':'Чего ты хочешь!?',
}
for i in range(1,11):
    MANUAL[f'FLOOR {i}']=f'ЭТАЖ {i}';MANUAL[f'>  FLOOR {i}']=f'>  ЭТАЖ {i}'
    MANUAL[f'Floor {i} Hallway']=f'Коридор {i}-го этажа'
    MANUAL[f'VPN Level {i}']=f'VPN, уровень {i}'
for i in (2,3):MANUAL[f'Wifi Dongle Level {i}']=f'Wi-Fi адаптер, уровень {i}'
MANUAL['You are Clint Edwards, an investigative reporter for one of the leading online News sites. You are investigating the mysterious disappearances and murders related to the deep web. You are deep in your case and about to make a breakthrough, \nbut then you get a call from someone least expected...']='Вы — Клинт Эдвардс, журналист одного из ведущих новостных сайтов. Вы расследуете загадочные исчезновения и убийства, связанные с даркнетом. Расследование близится к прорыву,\nно тут вам звонит человек, от которого вы меньше всего ожидали звонка...'
MANUAL.update({
'I forgot to mention about DOS Coin, DOS Coin is a cryptocurrency used on the deep web. You will need DOS Coin to purchase upgrades and items to help you on your way.':'Я забыл рассказать о DOS Coin — криптовалюте даркнета. Она понадобится тебе для покупки улучшений и полезных устройств.',
'If you look to the top left corner of your screen, this is how much DOS Coin you currently have. To help you out a little bit  I went ahead and purchased you a remote VPN. ':'В левом верхнем углу экрана показано, сколько у тебя DOS Coin. Чтобы немного помочь, я купил тебе удалённый VPN.',
'A remote VPN is a device that generates you DOS Coin during a certain period of time. Hackers will rent these devices from you to do their deeds. Depending on the location you place it at will determine the amount of DOS Coin you generate. So be sure to place it at a good location in your apartment complex. You can see what it generates under the DOS Coin menu by clicking on the DOS Coin logo. ':'Удалённый VPN — устройство, приносящее DOS Coin. Хакеры будут арендовать его у тебя для своих дел. Доход зависит от места установки, поэтому найди подходящую точку в доме. Чтобы посмотреть доход, нажми на значок DOS Coin.',
'Now any hardware item you purchase from the Shadow Market will be delivered via deep web drone, to your dead drop location. That is where your remote vpn is now located, to get there simply exit the lobby. Once you have picked up the package, the items will be available to you in your apartment. So be sure to look around your apartment when you get back from the dead drop.':'Все устройства с Теневого рынка доставляются дроном в тайник. Твой удалённый VPN уже там. Чтобы добраться до тайника, выйди из вестибюля. После получения посылки устройства появятся в квартире. Вернувшись, осмотрись.',
'That�s about it.':'На этом всё.',
'I heard you were looking for me..Check this out.. It might help you on your case':'Слышал, ты меня искал... Посмотри на это. Возможно, пригодится для твоего расследования.',
'Ok, I managed to source up the tunnel she used and placed it on your desktop. Unlocking this should reveal the location of where she is being held. The site seems to have a cut off time at 4 AM tonight!, after that.. I am afraid of what will happen to her.':'Я нашёл туннель, которым она пользовалась, и поместил его на рабочий стол. Разблокируй его, чтобы узнать, где её держат. Похоже, сайт закроется сегодня в четыре утра. Боюсь представить, что случится с ней после этого.',
'The tunnel is locked using a shadow web encryption key, the key will be broken down to 8 different hashes scattered across the deep web. You must explore the deep web and find these hashes. A hidden hash will look like this.':'Туннель защищён ключом шифрования теневой сети. Ключ разделён на восемь хешей, разбросанных по даркнету. Найди их все. Скрытый хеш выглядит вот так.',
'Each hash will have an index value associated with it, you must keep this in mind while you compile the master key. So if you were to find a hash that begins with the number 1, it will be the first sequence in the master key.':'У каждого хеша есть порядковый номер. Учитывай его при сборке главного ключа: хеш с номером 1 должен стоять первым.',
'Now a hash can be hidden anywhere on a page even in plain sight. So be sure to check the page thoroughly. Hover your mouse over everything and see if it will activate a hidden hot zone. I would even check the pages source code if I were you.':'Хеш может быть спрятан где угодно на странице — даже на самом видном месте. Проверяй всё внимательно. Наводи курсор на разные элементы: возможно, найдёшь скрытую активную область. На твоём месте я проверял бы и исходный код страниц.',
'Another tricky thing about the deep web is that some pages will only be available during a certain time window. So if you come across a page that is down, be sure to check back later.':'Есть ещё одна хитрость: некоторые страницы даркнета доступны только в определённое время. Если сайт не открывается, вернись к нему позже.',
'Upon your search, you may come across.. threats.. I left some documents on your desktop with more information on that. \n\nGood Luck...':'Во время поисков ты можешь столкнуться... с угрозами. Я оставил на рабочем столе документы с подробностями.\n\nУдачи...',
'Oh wait.. Here comes a new girl..':'Подожди... Вот появилась новая девушка...',
})

SAFE_FIELDS={
'Text':{'m_Text'},'TextMeshProUGUI':{'m_text'},'TutorialStepDefinition':{'Text'},
'WebSiteDefinition':{'PageTitle','PageDesc'},'WebPageDefinition':{'PageName'},
'ZeroDayProductDefinition':{'productName','productDesc'},'ShadowMarketProductDefinition':{'productName','productDesc'},
'TenantDefinition':{'tenantNotes'},'TerminalLineDefinition':{'terminalText'},'EndingResponseDefinition':{'ResponseOption'},
'SoftwareProductDefinition':{'ProductTitle','MinProductTitle'},'DocDefinition':{'Title'},
}
# Keep untranslated pages whose narrative includes sexual exploitation of minors.
EXCLUDED_DIRS={'littlefriends','mydaughter','hiddenpleasures','granddaddy','genshare','pantysales','ilovecats','dronespy','cleanup'}
def unsafe_text(t):
    return bool(re.search(r'(?i)\b(child|children|underage|little girls?|young girls?|\d{1,2}[ -]year[ -]old|pedo\w*)\b',t) and re.search(r'(?i)\b(sex\w*|fuck\w*|nude\w*|naked|rape\w*|porn\w*|virgin\w*|pleasure\w*)\b',t)) or bool(re.search(r'(?i)\bCP\b',t) and re.search(r'(?i)\b(girls?|school|download\w*)\b',t))
def translatable(t):
    t=t.strip()
    if not re.search(r'[A-Za-z]{2}',t):return False
    if re.search(r'[A-Za-z0-9+/]{28,}',t):return False
    if not re.search(r'\s',t) and len(t)>18:return False
    if sum(c.isalpha() for c in t)<2:return False
    if re.fullmatch(r'(?:https?://\S+|\S+\.(?:ann|onion)|[a-f0-9]{20,}|[A-Z0-9_]{15,})',t):return False
    if t in {'skyBREAK','memD3FR4G3R','N0D3H3X3R','stackPUSHER','ZONEWALL','ZoneWall','A.N.N','zeroDay','NOIRTUNNEL','WEP','WPA','WPA2','EAPOL HMAC','LOL','N/A','DOS Coin'}:return False
    if re.fullmatch(r'[>\s]*(?:exit|scan|clear|help|quit|list|WEP|WPA|WPA2|skyBREAK)(?:\s*>\s*)?',t,re.I):return False
    if t.startswith('skyBREAK >'):return False
    # ASCII art and numeric/cipher puzzles remain exact.
    if len(t)>600 and sum(c.isalpha() for c in t)/len(t)<.55:return False
    return True

class PageParser(HTMLParser):
    def __init__(self,source):
        super().__init__(convert_charrefs=False);self.source=source;self.parts=[];self.stack=[];self.lines=[0]
        self.lines += [m.end() for m in re.finditer('\n',source)]
        self.feed(source)
    def pos(self):
        line,col=self.getpos();return self.lines[line-1]+col
    def handle_starttag(self,tag,attrs):
        if tag not in ('br','hr','img','input','meta','link','source','area','embed','wbr','col','base','param'):self.stack.append(tag)
        raw=self.get_starttag_text();at=self.pos()
        attrdict=dict(attrs)
        for m in re.finditer(r'\b(title|alt|placeholder|value)\s*=\s*([\"\'])(.*?)\2',raw,re.I|re.S):
            if m[1].lower()=='value' and not (tag=='input' and attrdict.get('type','').lower() in ('submit','button','reset')):continue
            self.parts.append((at+m.start(3),at+m.end(3),m[3],'attr'))
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if self.stack and self.stack[-1]==tag:self.stack.pop()
    def handle_endtag(self,tag):
        if tag in self.stack:self.stack=self.stack[:len(self.stack)-1-self.stack[::-1].index(tag)]
    def handle_data(self,data):
        if any(t in self.stack for t in ('script','style','pre','code','textarea')):return
        if data.strip():self.parts.append((self.pos(),self.pos()+len(data),data,'text'))

def html_parts(source):
    restricted=unsafe_text(source)
    parts=[(a,b,t,kind) for a,b,t,kind in PageParser(source).parts if translatable(html.unescape(t))]
    # Cipher blocks contain short pieces separated by the game's hash-placement
    # tags. Protect the entire enclosing paragraph, not just long base64 runs.
    protected=[]
    for match in re.finditer(r'<(?:p|pre|textarea)\b[^>]*>.*?</(?:p|pre|textarea)>',source,re.S|re.I):
        plain=html.unescape(re.sub(r'<[^>]+>','',match[0]))
        if '-----BEGIN PGP' in plain or re.search(r'[A-Za-z0-9+/]{28,}',plain):
            protected.append((match.start(),match.end()))
    parts=[p for p in parts if not any(a<=p[0]<b for a,b in protected)]
    if restricted:
        parts=[p for p in parts if not re.search(r'(?i)\b(child\w*|underage|girls?|young|sex\w*|fuck\w*|nude\w*|naked|rape\w*|porn\w*|virgin\w*|pleasure\w*|breed\w*|teen\w*|\d{1,2}[ -]year[ -]old)\b',p[2])]
    return parts

corpus=set()
def add(t):
    if translatable(t) and not unsafe_text(t):corpus.add(html.unescape(t).strip())
rows=json.loads((OUT/'asset-strings.json').read_text(encoding='utf-8'))
for row in rows:
    if row['path'][0] in SAFE_FIELDS.get(row['class'],set()) and len(row['path'])==1:add(row['text'])
    elif row['path']==['PageHTML']:
        for _,_,t,_ in html_parts(row['text']):add(t)
from release_config import original_path
pack=read_pack(original_path('Resources/browser_assets'))
excluded_html={re.sub(r'\s+','',data.decode('utf-8-sig')) for name,data in pack.items() if name.endswith('.html') and name.split('/')[1].lower() in EXCLUDED_DIRS}
html_source_names={re.sub(r'\s+','',data.decode('utf-8-sig')):name for name,data in pack.items() if name.endswith('.html')}
def visible_key(source):
    source=re.sub(r'<(?:head|script|style)\b[^>]*>.*?</(?:head|script|style)>','',source,flags=re.S|re.I)
    return re.sub(r'\s+','',html.unescape(re.sub(r'<[^>]+>','',source)))
visible_source_names={visible_key(data.decode('utf-8-sig')):name for name,data in pack.items() if name.endswith('.html')}
context_file=OUT/'editorial-context.json'
context_edits=json.loads(context_file.read_text('utf-8')) if context_file.exists() else {}
for name,data in pack.items():
    if name.endswith('.html') and name.split('/')[1].lower() not in EXCLUDED_DIRS:
        for _,_,t,_ in html_parts(data.decode('utf-8-sig',errors='strict')):add(t)
code=json.loads((OUT/'code-strings.json').read_text(encoding='utf-8-sig'))
def code_visible(row):
    typ,method,t=row['Type'],row['Method'],row['Text']
    if typ.startswith('skyBreak') and method not in ('ProcessCMD',) and translatable(t):return True
    if typ in ('NoirTunnelBehaviour','ShadowMarketProductsBTNBehaviour','ZeroDayProductBTNBehaviour','ComputerPowerHook','ShadowProductObject','VPNMenuObject','LoadingScreenManager') and not t.startswith('_'):return translatable(t)
    if typ=='MagicSlinger' and method in ('GetFriendlyLocationName','GetNetworkSecurityType','GetWifiSiginalType'):return t in MANUAL
    if typ=='TenantTrackManager' and method=='updateTenantData':return t.strip()=='FLOOR'
    if (typ,method) in {('MemDeFragHack','PrepAttack'),('StackPusherHack','PrepStackPusherAttack'),('SweeperHack','PrepSweepAttack')}:
        return t.strip().startswith('Loading ') or t.strip()=='Initialzing...'
    return t in ('YOU WERE KILLED','YOU DISAPPOINTED THE DOLL MAKER','TIMES UP!')
for row in code:
    if code_visible(row):add(row['Text'])

cache_path=OUT/'translations.json'
cache=json.loads(cache_path.read_text(encoding='utf-8')) if cache_path.exists() else {}
for k,v in MANUAL.items():cache.setdefault(k.strip(),v.strip())
PROTECT=re.compile(r'<[^>\n]+>|\{[^{}]+\}|https?://\S+|\b(?:DOS Coins?|DOSCoin|skyBREAK|memD3FR4G3R|N0D3H3X3R|stackPUSHER|ZONEWALL|ZoneWall|A\.N\.N|NOIRTUNNEL|zeroDay|FacePage|WEP|WPA2?|BSSID|ESSID|EAPOL|HMAC|StartPort|EndPort|OpenPort|StartingPort|EndingPort|CH|PWR|SIG|LIST|De-Auth)\b')
def protect(t):
    tokens=[]
    def sub(m):
        tokens.append(m[0]);return f'ZXQ{len(tokens)-1:04d}QXZ'
    return PROTECT.sub(sub,t),tokens
def restore(t,tokens):
    for i,v in enumerate(tokens):
        pattern=r'ZXQ\s*'+f'{i:04d}'+r'\s*QXZ'
        t,n=re.subn(pattern,lambda m:v,t,flags=re.I)
        if n!=1:raise ValueError('Lost protected token '+str(i))
    return t
def translate_batch(batch):
    encoded=[];token_lists=[]
    for i,t in enumerate(batch):
        t,tokens=protect(t);token_lists.append(tokens);encoded.append(f'ZXB{i:04d}BXZ '+re.sub(r'\s+',' ',t))
    q='\n'.join(encoded)
    url='https://translate.googleapis.com/translate_a/single?'+urllib.parse.urlencode({'client':'gtx','sl':'en','tl':'ru','dt':'t','q':q})
    for attempt in range(4):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
            result=json.load(urllib.request.urlopen(req,timeout=35));text=''.join(x[0] for x in result[0] if x[0])
            marks=list(re.finditer(r'ZXB\s*(\d{4})\s*BXZ\s*',text,re.I))
            if len(marks)!=len(batch):raise ValueError('Batch delimiter lost')
            output={}
            for i,m in enumerate(marks):
                if int(m[1])!=i:raise ValueError('Wrong batch order')
                ru=text[m.end():marks[i+1].start() if i+1<len(marks) else len(text)].strip()
                output[batch[i]]=restore(ru,token_lists[i])
            return output
        except Exception:
            if attempt==3:
                if len(batch)>1:
                    mid=len(batch)//2;return translate_batch(batch[:mid])|translate_batch(batch[mid:])
                source=batch[0];chunks=[]
                for part in re.split(r'(?<=[.!?])\s+',re.sub(r'\s+',' ',source)):
                    if chunks and len(chunks[-1])+len(part)<2400:chunks[-1]+=' '+part
                    else:chunks.append(part)
                translated=[]
                for part in chunks:
                    query,tokens=protect(part)
                    direct='https://translate.googleapis.com/translate_a/single?'+urllib.parse.urlencode({'client':'gtx','sl':'en','tl':'ru','dt':'t','q':query})
                    data=json.load(urllib.request.urlopen(direct,timeout=35))
                    translated.append(restore(''.join(x[0] for x in data[0] if x[0]),tokens))
                return {source:' '.join(translated)}
            time.sleep(1+attempt*2)

def tr(t):
    clean=html.unescape(t).strip()
    if clean not in cache or (not cache[clean].strip() and clean.lower() not in {'the','a','an'}):return t
    prefix=t[:len(t)-len(t.lstrip())];suffix=t[len(t.rstrip()):]
    return prefix+cache[clean]+suffix
def tr_html(source,page=None):
    if re.sub(r'\s+','',source) in excluded_html:return source
    page=page or html_source_names.get(re.sub(r'\s+','',source),'') or visible_source_names.get(visible_key(source),'')
    if page and page.split('/')[1].lower() in EXCLUDED_DIRS:return source
    context=context_edits.get(page.split('/')[1].lower(),{}) if page else {}
    from paragraph_patch import replacements
    paragraph_changes=replacements(source,PageParser)
    parts=html_parts(source)
    titles=[(m.start(),m.end()) for m in re.finditer(r'<title\b[^>]*>.*?</title>',source,re.S|re.I)]
    from preserve_names import preserve
    from paragraph_inventory import plain
    titles.extend((m.start(),m.end()) for m in re.finditer(r'<(?:h1|h2|h3|h4)\b[^>]*>.*?</(?:h1|h2|h3|h4)>',source,re.S|re.I) if preserve(plain(m[0])))
    parts=[p for p in parts if not any(a<=p[0]<b for a,b in titles)]
    known={(a,b) for a,b,t,kind in parts}
    parts.extend((a,b,source[a:b],'text') for a,b in paragraph_changes if (a,b) not in known)
    for a,b,t,kind in sorted(parts,reverse=True):
        key=html.unescape(t).strip()
        if (a,b) in paragraph_changes or key in context or key in cache:
            if (a,b) in paragraph_changes:ru=paragraph_changes[(a,b)]
            elif key in context:
                ru=t[:len(t)-len(t.lstrip())]+context[key]+t[len(t.rstrip()):]
            else:ru=tr(t)
            source=source[:a]+html.escape(ru,quote=kind=='attr')+source[b:]
    from navigation_captions import patch
    source=patch(source,page)[0]
    if page=='/NotFound/index.html':
        from browser_error_page import patch as error_page
        source=error_page(source)
    return source

if __name__=='__main__':
    todo=sorted(corpus-cache.keys());print('Unique strings',len(corpus),'pending',len(todo),'chars',sum(map(len,todo)),flush=True)
    batches=[];batch=[];size=0
    for t in todo:
        if batch and (size+len(t)>2400 or len(batch)>=28):batches.append(batch);batch=[];size=0
        batch.append(t);size+=len(t)+20
    if batch:batches.append(batch)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(translate_batch,b):b for b in batches}
        for i,f in enumerate(concurrent.futures.as_completed(futures)):
            cache.update(f.result());cache_path.write_text(json.dumps(cache,ensure_ascii=False,indent=2),encoding='utf-8')
            print('Translated batches',i+1,'/',len(batches),flush=True)
    print('DONE',len(cache),flush=True)
