import html,json,re,unicodedata
from pathlib import Path
from paragraph_inventory import plain

def replacements(source,parser_type):
    path=Path(__file__).parent/'paragraph-edits.json'
    if not path.exists():return {}
    translations=json.loads(path.read_text('utf-8'))
    output={}
    class Parser(parser_type):
        def handle_data(self,data):
            if data and not data.strip() and not any(t in self.stack for t in ('script','style','pre','code','textarea')):
                self.parts.append((self.pos(),self.pos()+len(data),data,'space'))
            else:super().handle_data(data)
        def handle_entityref(self,name):
            self.parts.append((self.pos(),self.pos()+len(name)+2,'','entity'))
        def handle_charref(self,name):
            self.parts.append((self.pos(),self.pos()+len(name)+3,'','entity'))
    def assign(fragment,translated,offset,key):
        parts=[p for p in Parser(fragment).parts if p[3]!='attr']
        nodes=[p for p in parts if p[3] not in ('entity','space')]
        words=translated.split();weights=[max(1,len(html.unescape(p[2]).split())) for p in nodes];characters=False
        if not nodes:
            if words:raise ValueError('Missing paragraph text nodes: '+key[:60])
            return
        required=set(range(len(nodes)))
        if len(words)<len(nodes):
            required=set()
            for anchor in re.finditer(r'<a\b[^>]*\bclass\s*=\s*[\"\'][^\"\']*\bC[PF]TAG\b[^\"\']*[\"\'][^>]*>.*?</a>',fragment,re.S|re.I):
                inside=[i for i,p in enumerate(nodes) if anchor.start()<=p[0]<anchor.end()]
                if inside:required.add(inside[0])
            if len(words)<len(required):
                # Russian often needs fewer words. Keep every hash anchor by
                # splitting grapheme clusters across inline tags; the visible
                # phrase remains exactly the editor's natural translation.
                characters=True;words=[]
                for c in translated.strip():
                    if (unicodedata.category(c).startswith('M') or c.isspace()) and words:words[-1]+=c
                    else:words.append(c)
                weights=[max(1,len(html.unescape(p[2]).strip())) for p in nodes]
                if len(words)<len(required):raise ValueError('Too few glyphs for hash anchors: '+key[:60])
        weight_total=sum(weights);position=0;accumulated=0
        for i,(a,b,t,kind) in enumerate(nodes):
            accumulated+=weights[i]
            reserve=sum(j>i for j in required)
            end=min(len(words)-reserve,max(position+(1 if i in required else 0),round(accumulated/weight_total*len(words))))
            output[(offset+a,offset+b)]=(''.join(words[position:end]) if characters else ' '.join(words[position:end])+(' ' if end>position and end<len(words) else ''))
            position=end
        assert position==len(words)
        for a,b,t,kind in parts:
            if kind in ('entity','space'):output[(offset+a,offset+b)]=''
    for paragraph in re.finditer(r'<(?P<tag>p|h1|h2|h3|h4|label|button)\b[^>]*>.*?</(?P=tag)>',source,re.S|re.I):
        key=plain(paragraph[0])
        if key not in translations:continue
        # Actual navigation links retain the meaning of their labels. These
        # prose paragraphs contain only decorative hash-placement anchors.
        if re.search(r'\b(?:href|onclick)\s*=',paragraph[0],re.I):
            raise ValueError('Paragraph override contains a navigation link: '+key[:60])
        if re.search(r'<br\s*/?>',paragraph[0],re.I):
            groups=re.split(r'<br\s*/?>',paragraph[0],flags=re.I)
            if '\n' in translations[key]:
                targets=translations[key].split('\n')
                if len(groups)!=len(targets):
                    nonempty=[t for t in targets if t.strip()]
                    if sum(bool(plain(g)) for g in groups)!=len(nonempty):raise ValueError('Translated line-break count differs: '+key[:60])
                    iterator=iter(nonempty);targets=[next(iterator) if plain(g) else '' for g in groups]
            else:
                # Never introduce a line break in the middle of a Russian word.
                words=translations[key].split();weights=[len(plain(g).split()) for g in groups]
                position=0;accumulated=0;targets=[];total=sum(weights)
                if len(words)<sum(bool(w) for w in weights):raise ValueError('Too few words for line groups: '+key[:60])
                for i,w in enumerate(weights):
                    accumulated+=w;reserve=sum(bool(v) for v in weights[i+1:])
                    end=min(len(words)-reserve,max(position+int(bool(w)),round(accumulated/total*len(words)))) if w else position
                    targets.append(' '.join(words[position:end]));position=end
                assert position==len(words)
            offset=paragraph.start()
            breaks=list(re.finditer(r'<br\s*/?>',paragraph[0],re.I))
            for i,(fragment,translated) in enumerate(zip(groups,targets)):
                assign(fragment,translated,offset,key)
                offset=paragraph.start()+breaks[i].end() if i<len(breaks) else offset
        else:assign(paragraph[0],translations[key],paragraph.start(),key)
    return output
