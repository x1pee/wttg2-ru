import io,math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent/'deps'))
import numpy as np
from scipy.ndimage import distance_transform_edt
from PIL import Image,ImageDraw,ImageFont
from fontTools.ttLib import TTFont

CASCADIA=Path(r'C:\Windows\Fonts\CascadiaCode.ttf')
FONT_BYTES=CASCADIA.read_bytes()
CYRILLIC=set(range(0x410,0x450))|{0x401,0x451}
def covers_ru(data):
    return bool(data) and CYRILLIC.issubset(TTFont(io.BytesIO(bytes(data))).getBestCmap())

def replace_dynamic_font(tree):
    tree['m_FontData']=list(FONT_BYTES)
    tree['m_FontNames']=['Cascadia Code']
    tree['m_CharacterRects']=[];tree['m_KerningValues']=[]
    tree['m_Texture']={'m_FileID':0,'m_PathID':0}
    tree['m_AsciiStartOffset']=0;tree['m_ConvertCase']=-2
    tree['m_FontRenderingMode']=0

def make_sdf_font(tree,characters):
    info=tree['m_fontInfo'];nominal=info['PointSize'];cap=info['CapHeight']
    initial=ImageFont.truetype(str(CASCADIA),round(nominal))
    box=initial.getbbox('H',anchor='ls');scale=cap/(box[3]-box[1]);px=max(12,round(nominal*scale))
    font=ImageFont.truetype(str(CASCADIA),px)
    chars=sorted(set(range(32,127))|CYRILLIC|set(characters)|{0x2013,0x2014,0x2026,0x2018,0x2019,0x201c,0x201d,0xab,0xbb,0x2116})
    cmap=TTFont(str(CASCADIA)).getBestCmap();chars=[c for c in chars if c in cmap]
    pad=6;tiles=[]
    for code in chars:
        char=chr(code);left,top,right,bottom=font.getbbox(char,anchor='ls')
        width=max(1,right-left);height=max(1,bottom-top)
        tile=Image.new('L',(width+2*pad,height+2*pad))
        if char!=' ':ImageDraw.Draw(tile).text((pad-left,pad-top),char,font=font,fill=255,anchor='ls')
        mask=np.array(tile)>127
        if char==' ':sdf=np.zeros(mask.shape,dtype=np.uint8)
        else:
            distance=distance_transform_edt(mask)-distance_transform_edt(~mask)
            sdf=np.clip(128+distance*127/pad,0,255).astype(np.uint8)
        tiles.append((code,left,top,width,height,float(font.getlength(char)),Image.fromarray(sdf)))
    side=512
    while True:
        x=y=1;rowheight=0;positions=[]
        for tile in tiles:
            w,h=tile[-1].size
            if x+w+1>side:x=1;y+=rowheight+1;rowheight=0
            positions.append((x,y));x+=w+1;rowheight=max(rowheight,h)
        if y+rowheight+1<=side:break
        side*=2
        if side>4096:raise ValueError('Atlas too large')
    atlas=Image.new('L',(side,side));glyphs=[]
    for (code,left,top,width,height,advance,tile),(x,y) in zip(tiles,positions):
        atlas.paste(tile,(x,y))
        glyphs.append({'id':code,'x':float(x+pad),'y':float(y+pad),
            'width':float(width),'height':float(height),'xOffset':float(left),'yOffset':float(-top),
            'xAdvance':advance,'scale':1.0})
    tree['m_glyphInfoList']=glyphs;tree['m_kerningInfo']['kerningPairs']=[]
    info['Name']='WTTG2 RU Mono';info['CharacterCount']=len(glyphs);info['Padding']=float(pad)
    info['AtlasWidth']=float(side);info['AtlasHeight']=float(side)
    tree['normalStyle']=0;tree['boldStyle']=.75
    return atlas
