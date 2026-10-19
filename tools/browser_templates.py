import html,re
from translate_game import PageParser
TEXTS={
 'Load Error':'Ошибка загрузки','Page Crashed':'Страница перестала отвечать',
 'The renderer process for this page is no longer running.':'Процесс отображения этой страницы завершился.',
 'JavaScript Alert':'Сообщение сайта','JavaScript Confirmation':'Подтверждение',
 'Confirm Page Navigation':'Выход со страницы','The page says:':'Сообщение страницы:',
 'Do you want to leave this page?':'Покинуть эту страницу?',
 'Leave':'Покинуть','Stay':'Остаться','Confirm Page Reload':'Обновление страницы',
 'Do you want to reload this page?':'Обновить эту страницу?','Reload':'Обновить',
 'JavaScript Prompt':'Ввод данных','Authentication Prompt':'Вход на сайт',
 'User name:':'Имя пользователя:','Password:':'Пароль:','Log In':'Войти',
 'Cancel':'Отмена','OK':'ОК',
}
MENU={'Back':'Назад','Forward':'Вперёд','Reload':'Обновить','Cut':'Вырезать',
      'Copy':'Копировать','Paste':'Вставить','Select All':'Выделить всё',
      'Undo':'Отменить','Redo':'Повторить','Delete':'Удалить',
      'Copy link address':'Копировать адрес ссылки','Copy image':'Копировать изображение',
      'Copy image address':'Копировать адрес изображения','Open link in new tab':'Открыть ссылку в новой вкладке'}
def patch(name,source):
    if name not in ('Errors','Dialogs'):return source
    for a,b,en,kind in reversed(PageParser(source).parts):
        key=html.unescape(en).strip()
        if key in TEXTS:
            ru=en[:len(en)-len(en.lstrip())]+TEXTS[key]+en[len(en.rstrip()):]
            source=source[:a]+html.escape(ru,quote=kind=='attr')+source[b:]
    if name=='Errors':
        source=source.replace('"Failed to load " + info.url','"Не удалось загрузить " + info.url')
    if name=='Dialogs':
        import json
        source=source.replace('itemEl.textContent = item.label.replace(/&/g, "");',
         'var ruLabels = '+json.dumps(MENU,ensure_ascii=False)+';\n\t\t\tvar visibleLabel = item.label.replace(/&/g, "");\n\t\t\titemEl.textContent = ruLabels[visibleLabel] || visibleLabel;')
    return source
