def patch_title_layout(env,counts):
    # UI coordinates are authored in pixels within the existing screen-space canvas.
    def rect(pid,pos=None,size=None,anchor=None,pivot=None):
        obj=env.file.objects[pid];tree=obj.read_typetree()
        if pos is not None:tree['m_AnchoredPosition']={'x':float(pos[0]),'y':float(pos[1])}
        if size is not None:tree['m_SizeDelta']={'x':float(size[0]),'y':float(size[1])}
        if anchor is not None:tree['m_AnchorMin']=tree['m_AnchorMax']={'x':float(anchor[0]),'y':float(anchor[1])}
        if pivot is not None:tree['m_Pivot']={'x':float(pivot[0]),'y':float(pivot[1])}
        obj.save_typetree(tree);counts['LayoutRects']+=1
    def text(pid,value=None,font=22,align=513,minsize=None):
        obj=env.file.objects[pid];node=obj.generate_monobehaviour_node();tree=obj.read_typetree(nodes=node)
        if value is not None:tree['m_text']=value
        tree['m_fontSize']=float(font);tree['m_fontSizeMax']=float(font)
        tree['m_fontSizeMin']=float(minsize if minsize else font)
        tree['m_enableAutoSizing']=minsize is not None
        tree['m_enableWordWrapping']=False;tree['m_textAlignment']=align
        tree['m_characterSpacing']=0;tree['m_lineSpacing']=0
        obj.save_typetree(tree,nodes=node)
    rect(478,(0,-86),(700,216));rect(468,(0,-330),(700,108))
    labels=[(480,587,'Качество графики',0),(494,611,'Разрешение',-54),
            (503,623,'V-Sync',-108),(504,624,'Оконный режим',-162),
            (491,608,'Микрофон',0),(509,630,'Нагота',-54)]
    for rt,pid,label,y in labels:
        rect(rt,(0,y),(245,44));text(pid,label,font=22,align=513)
    rect(514,(260,-14),(220,16));rect(474,(260,-68),(220,16))
    rect(463,(504,0),(190,44));rect(489,(504,-54),(190,44))
    text(558,'Очень высокое',font=18,align=513);text(607,'1920 × 1080',font=18,align=513)
    toggles=[(475,492,609,481,505,625,-108),(511,519,656,477,482,591,-162),
             (501,465,562,483,510,631,0),(464,498,614,485,461,554,-54)]
    for on,onrt,ont,off,offrt,offt,y in toggles:
        rect(on,(260,y),(80,44));rect(off,(372,y),(80,44))
        # Keep text and clickable region the same size; 32 px separates the options.
        for rt,pid,label in [(onrt,ont,'Вкл'),(offrt,offt,'Выкл')]:
            rect(rt,(0,0),(80,44));text(pid,label,font=22,align=514)
    rect(455,(476,0),(224,48))
    mic=env.file.objects[548];node=mic.generate_monobehaviour_node();tree=mic.read_typetree(nodes=node)
    tree['m_Text']='Некоторые игровые механики станут сложнее.';tree['m_FontData']['m_FontSize']=13;tree['m_FontData']['m_BestFit']=False;tree['m_FontData']['m_Alignment']=3;mic.save_typetree(tree,nodes=node)
    rect(472,(0,-12),(0,54));text(569,'НАСТРОЙКИ',font=40,align=514)
    rect(462,(-130,-462),(160,48),anchor=(.5,1),pivot=(.5,1));rect(518,(110,-462),(220,48))
    rect(484,(0,0),(160,48));rect(488,(0,0),(220,48));text(595,'НАЗАД',font=24,align=514);text(606,'ПРИМЕНИТЬ',font=24,align=514)
    for button,rt,pid,label in [(479,495,612,'НОВАЯ ИГРА'),(486,456,550,'ПРОДОЛЖИТЬ'),(515,500,616,'НАСТРОЙКИ'),(513,467,564,'ВЫХОД')]:
        rect(button,size=(330,75));rect(rt,(0,0),(330,75));text(pid,label,font=42,align=516,minsize=32)
