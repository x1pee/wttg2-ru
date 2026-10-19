def patch(source):
    source=source.replace('<title>Problem loading page</title>','<title>Ошибка загрузки страницы</title>')
    return source.replace('<div id="NotFound"></div>','''<div id="NotFound" role="alert" style="background-image:none;width:calc(100% - 48px);max-width:721px;height:auto;margin:14vh auto 0;box-sizing:border-box;padding:24px;color:#404b55;font-size:17px;line-height:1.5;font-family:'Cascadia Code',WTTG2RU,monospace">
<div role="heading" aria-level="1" style="font-size:28px;line-height:1.2;margin-bottom:24px">Не удалось подключиться</div>
<div style="margin-bottom:14px">A.N.N не может установить соединение с этим сервером.</div>
<div style="margin-bottom:12px">• Возможно, сайт временно недоступен или перегружен. Попробуйте открыть его позже.</div>
<div style="margin-bottom:12px">• Если не открывается ни одна страница, проверьте подключение компьютера к сети.</div>
<div>• Если соединение защищено брандмауэром или прокси, убедитесь, что браузеру A.N.N разрешён доступ к сети.</div>
</div>''')
