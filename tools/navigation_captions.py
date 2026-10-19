import html,json,re
from html.parser import HTMLParser
from pathlib import Path
from posixpath import normpath
LABELS={
 'index.html':'Главная','store.html':'Магазин','shop.html':'Магазин','faq.html':'Вопросы',
 'join.html':'Вступить','signup.html':'Вступить','login.html':'Войти','sign.html':'Войти',
 'contact.html':'Контакты','order.html':'Заказать','quality.html':'Качество',
 'containers.html':'Ёмкости','specials.html':'Особые предложения','special.html':'Особые предложения',
 'confiscated.html':'Изъятые','leaked.html':'Утечки','contribute.html':'Передать',
 'purchase.html':'Оплатить','buy.html':'Купить','walletid.html':'Кошелёк',
 'myfavoritefeet.html':'Любимое','homemade.html':'Мои снимки','sendmepics.html':'Прислать фото',
 'page2.html':'Страница 2','page3.html':'Страница 3','creepy.html':'Жуткое',
 'posture.html':'Осанка','evilmonster.html':'Чудовище','how.html':'Как это сделано',
 'walk.html':'Продолжить','enter.html':'Войти','return.html':'Назад',
}
ALT={'home':'Главная','store':'Магазин','shop':'Магазин','join':'Вступить','join us':'Вступить',
     'login':'Войти','log in':'Войти','contact':'Контакты','submit':'Отправить','send':'Отправить',
     'faq':'Вопросы','buy':'Купить','buy now':'Купить','back':'Назад','next':'Далее','leave':'Выйти'}
ALT.update({value.lower():value for value in list(ALT.values())})
ALT['купить сейчас']='Купить'
# These image captions were inspected visually. Site logos, cipher images,
# photos and all other artwork remain untouched. Keys include the site folder
# to distinguish generic names such as images/button.jpg.
KNOWN_UI={
 '/brutal/images/button1.jpg':'Смотреть',
 '/bugchaser/images/login.jpg':'Войти',
 '/crybitch/images/button.jpg':'Войти',
 '/evidencelocker/images/photos.png':'Утечки фото и видео',
 '/evidencelocker/images/confiscated.png':'Изъятые фото и видео',
 '/evidencelocker/images/contribute.png':'Прислать фото и видео',
 '/evilcollection/images/home.png':'Главная',
 '/evilcollection/images/images.png':'Изображения',
 '/evilcollection/images/links.png':'Ссылки',
 '/evilcollection/images/chat.png':'Чат',
 '/evilcollection/images/signup.jpg':'Регистрация',
 '/evilcollection/images/loginbutton.jpg':'Войти',
 '/evilcollection/images/buy.jpg':'Купить',
 '/evilcollection/images/enter.jpg':'Войти',
 '/heirloom/images/button1.gif':'Главная',
 '/heirloom/images/button1c.gif':'Качество',
 '/heirloom/images/button22.gif':'Особые предложения',
 '/heirloom/images/button28.gif':'Ёмкости',
 '/heirloom/images/button2b.gif':'Спецзаказы',
 '/mutilation/images/access.png':'Доступ — 5 DOS Coin',
 '/mutilation/images/join.png':'Вступить',
}
_sizes={}
def image_info(attrs,page):
    if not page:return '',None
    ref=html.unescape(attrs.get('src','')).split('?',1)[0].split('#',1)[0]
    if not ref or '://' in ref:return '',None
    key=normpath(ref if ref.startswith('/') else page.rsplit('/',1)[0]+'/'+ref)
    if key.lower() not in KNOWN_UI:return key,None
    if key not in _sizes:
        from translate_game import pack
        from PIL import Image
        from io import BytesIO
        data=pack.get(key)
        if data is None:data=next((value for name,value in pack.items() if name.lower()==key.lower()),None)
        if data is None:raise ValueError('Known navigation image missing: '+key)
        with Image.open(BytesIO(data)) as image:_sizes[key]=image.size
    return key,_sizes[key]
class Attributes(HTMLParser):
    def __init__(self,source):super().__init__();self.attrs={};self.feed(source)
    def handle_starttag(self,tag,attrs):self.attrs.update(dict(attrs))
def candidates(source,page=None):
    used=[]
    for match in re.finditer(r'<a\b[^>]*>\s*<img\b[^>]*>\s*</a>',source,re.I|re.S):
        image=re.search(r'<img\b[^>]*>',match[0],re.I);attrs=Attributes(image[0]).attrs
        target=re.search(r"LinkClick\(\s*['\"]([^'\"]+)",match[0])
        key,natural=image_info(attrs,page)
        known=KNOWN_UI.get(key.lower())
        if not target and not known:continue
        try:w=int(attrs.get('width','0'));h=int(attrs.get('height','0'))
        except ValueError:continue
        if known:
            w=w or natural[0]
            h=h or (round(natural[1]*w/natural[0]) if w!=natural[0] else natural[1])
        elif not(45<=w<=360 and 16<=h<=50) or 'logo' in attrs.get('src','').lower():continue
        label=known or ALT.get(attrs.get('alt','').strip().lower()) or LABELS.get(target[1].lower())
        if not label:continue
        used.append((match.start()+image.start(),match.start()+image.end()))
        yield match,image,attrs,label,w,h,target[1] if target else ''
    # The same proven captions are also used in form buttons and images with
    # their own callbacks. Their original image remains the click target.
    for match in re.finditer(r'<img\b[^>]*>',source,re.I|re.S):
        if any(a<=match.start()<b for a,b in used):continue
        attrs=Attributes(match[0]).attrs;key,natural=image_info(attrs,page)
        label=KNOWN_UI.get(key.lower())
        if not label or 'opacity:0' in attrs.get('style',''):continue
        try:w=int(attrs.get('width','0')) or natural[0];h=int(attrs.get('height','0')) or round(natural[1]*w/natural[0])
        except ValueError:continue
        yield match,re.search(r'<img\b[^>]*>',match[0],re.I|re.S),attrs,label,w,h,''
def patch(source,page=None):
    changes=[]
    for anchor,image,attrs,label,w,h,target in candidates(source,page):
        font=min(13,max(9,h//2-2))
        while len(label)*font*.61>w-8 and font>9:font-=1
        old=image[0]
        hidden_style=';position:absolute;left:0;top:0;width:100%;height:100%;opacity:0;pointer-events:auto'
        if 'style' in attrs:
            hidden=re.sub(r'\bstyle\s*=\s*([\"\'])(.*?)\1',lambda m:'style="'+html.escape(m[2]+hidden_style,quote=True)+'"',old,flags=re.I|re.S)
        else:
            hidden=re.sub(r'\s*/?>$','',old)+' style="'+hidden_style.lstrip(';')+'"'+('/>' if old.rstrip().endswith('/>') else '>')
        # Retain the original image reference and anchor callback. Its English
        # pixels are hidden beneath a real, selectable Unicode UI caption.
        span='<span data-wttg2-ru-nav="1" style="position:relative;display:inline-flex;align-items:center;justify-content:center;box-sizing:border-box;vertical-align:middle;width:'+str(w)+'px;height:'+str(h)+'px;padding:2px 4px;background:#171717;border:1px solid #666;border-radius:2px;color:#eee;font-size:'+str(font)+'px;font-family:inherit;line-height:1.05;text-align:center">'+hidden+'<span style="pointer-events:none">'+html.escape(label)+'</span></span>'
        a=anchor.start()+image.start();b=anchor.start()+image.end();changes.append((a,b,span))
    for a,b,value in sorted(changes,reverse=True):source=source[:a]+value+source[b:]
    return source,len(changes)
if __name__=='__main__':
    import translate_game as t
    rows=[]
    for name,data in t.pack.items():
        if not name.endswith('.html') or name.split('/')[1].lower() in t.EXCLUDED_DIRS:continue
        for a,image,attrs,label,w,h,target in candidates(data.decode('utf-8-sig'),name):
            rows.append(dict(page=name,target=target,image=attrs.get('src'),label=label,width=w,height=h))
    (Path(__file__).parent/'navigation-captions.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Navigation captions:',len(rows),'unique images:',len({(x['page'].split('/')[1],x['image']) for x in rows}))
    print(*rows[:16],sep='\n')
