from GetText import *
from imports import *
from init import *
warnings.filterwarnings("ignore")


def request_link_form(text_request, fl_Face):
    """ Функция формирования второй части ссылки запроса  """
    link_last = ''
    # Делим запрос на слова в нижнем регистре
    words_request = re.split(' ', text_request.lower())
    # Формируем начало ссылки ('&text=' + первое слово запроса)
    link_last += '&text='+words_request[0]
    # По всем словам запроса начиная со 2-го
    for word in words_request[1:]:
        link_last += '%20'+word
    # Если установлен поиск картинок с лицом:
    if fl_Face:
        link_last += '&type=face&from=tabbar'
    return link_last


# Добавляем разные запросы в список:
link_first = 'https://yandex.ru/images/search?p='          # первая часть ссылки
links_last = []
request_text = 'Требуется помощь ребенку'
links_last.append(request_link_form(request_text, True))
request_text = 'срочный сбор на лечение ребенка'
links_last.append(request_link_form(request_text, False))
print('Полученные ссылки на поиск картинок:\n', links_last)

# Сохраняем картинки из поисковых запросов по ключевым словам:
if not os.path.isdir(folder_path):
     os.mkdir(folder_path)           # Создаём каталог для сохр.картинок
if not os.path.isdir(folder_4_tables):
     os.mkdir(folder_4_tables)       # Создаём каталог для сохр.табличек


def parse(link):
    """ Парсим картинки """
    res = req.get(link, headers = HEADERS)
    html = BeautifulSoup(res.text, 'lxml')
    body_for_pictures = html.find('div', class_="page-layout") # тело с pics
    pictures = body_for_pictures.find_all('div', class_="serp-item")
    # Парсим ссылки на картинку в поисковом запросе яндекса
    yandex_search_link = []
    for a in body_for_pictures.find_all('a',
                                        class_ = 'serp-item__link', href=True):
        yandex_search_link.append('https://yandex.ru'+a['href'])
    return pictures, yandex_search_link


def get_links(pics,yandex_search_link):
    """ Забираем ссылки из pics """
    links, links_to_site, links_yandex = [], [], []
    for i, pic in enumerate(pics):
        # Ищем сайт с картинкой (вкладку с ней)
        link_to_site = re.findall('(?<=","url":").*?(?=",)', str(pic.get_text))
        if link_to_site:
            links_to_site.append(link_to_site[0])
            # Ищем прямую ссылку, только если нашли сайт c картинкой
            # (иначе может быть косяк, когда одна ссылка есть, а другой нет)
            link = re.findall('(?<="img_href":").*?(?=",)', str(pic.get_text))
            links_yandex.append(yandex_search_link[i])
            if link:
                links.append(link[0])         # Заполняем список ссылок
            else:
                links.append('error')
        else:
            links_to_site.append('-')
            links.append('-')
            links_yandex.append('-')
    return links, links_to_site, links_yandex


def save_pics(links):
    """ Сохраняем картинки по ссылкам """
    # 'C:/Users/alexk/Documents/'+ 'Parsing photos ya/Pictures_downloaded
    i = 0
    fl_saved = []  # Флаг - "Картинка сохранена". Имя
    for url in links:
        i += 1  # Порядковый номер картинки на странице
        filename = 'YA_' + str(req_num) + '_p' + str(page_num) + '_' + str(
            i) + '.jpg'  # Имя файла сохранения
        # Попытки соединения с сервером картинки:
        try:
            req.post(url, timeout=10)  # Запрос к картинке
            try:
                image_content = req.get(url,timeout=10).content  # Получаем pic
            except Exception as e:
                print(f"Невозможно загрузить картинку {url} — {e}")
            try:
                image_file = io.BytesIO(image_content)
                image = Image.open(image_file).convert('RGB')
                # Полный путь к файлу картинки:
                file_path = folder_path + '/' + filename
                with open(file_path, 'wb') as f:
                    image.save(f, "JPEG",
                               quality=50)  # Сохраняем pic, уменьшаем кач-во
                    print(filename[:-4], url, f"Сохранено как {filename}")
                    fl_saved.append(filename[:-4])
            except Exception as e:
                print(filename[:-4], url, f"Ошибка сохранения — {e}")
                fl_saved.append('-')
        except Exception:  # Если таймаут,пропускаем картинку
            print(filename[:-4], url, 'Нет ответа от сервера')
            fl_saved.append('-')
    return fl_saved


# Откуда начинаем парсить. Если прервались, эти переменные
# Заполняются последним запросом и страницей
num_link_stop = 0
page_stop = 0
pages = range(1,num_pages_to_parse+1)  # Кол-во обрабатываемых страниц в запросе
list_links_to_pics, list_links_to_websites, \
fls_saved, list_links_yandex = [], [], [], []
req_num = 0
break_ = False

for num_link, link_last in enumerate(
        links_last[num_link_stop:]):    # По каждому поискового запроса
    if break_:
        break
    req_num += 1                        # Порядковый номер запроса
    for page_num in pages[page_stop:]:  # По каждой странице поиск.запроса
        try:
            link = link_first + str(
                page_num) + link_last   # Собираем ссылку на страницу поиска
            # Получаем ссылку на картинки и ссылки на сайт:
            links_pic, links_to_website, links_yandex = get_links(
                parse(link)[0], parse(link)[1])
            fl_saved = save_pics(links_pic)        # Сохраняем картинку
            list_links_to_pics.extend(links_pic)   # Ссылки прямые на картинку
            list_links_to_websites.extend(
                links_to_website)                  # Ссылки на сайт с картинками
            list_links_yandex.extend(links_yandex) # Ссылки на похожие картинки
            fls_saved.extend(fl_saved)             # Имя сохраненной картинки
            if page_num != pages[-1]:
                time.sleep(20)  # Пауза между страницами, чтобы не откл.запросы
        except Exception as e:  # Если откл. запрос, сохр. тек.состояние цикла
            link_stop = link
            page_stop = page_num
            num_link_stop = num_link
            break_ = True
            print(f'Прервались на странице {page_stop}, ссылка {link_stop}')
            break
# смотрим, что получили
print('Полученные ссылки на поиск картинок:')
print(links_last)


def make_hyperlink(link, text):
    """ Функция создания гиперссылок для документа в Excel """
    return '=HYPERLINK("%s", "%s")'%(link, text)


# Делаем гиперссылки для кликабельности в документе Excel:
hyperlink_pics, hyperlink_websites =[], []
for link in list_links_to_pics:
    hyperlink_pics.append(make_hyperlink(link, str(link)))
for link in list_links_to_websites:
    hyperlink_websites.append(make_hyperlink(link, str(link)))

# Создаём датафрейм из полученных списков:
df = pd.DataFrame()
df['Имя картинки'] = fls_saved
df['Прямая ссылка'] = hyperlink_pics
df['Ссылка на сайт'] = hyperlink_websites
df['Ссылка на яндекс в поиске'] = list_links_yandex  # Без гиперссылки передаём

# Удаляем строки, где картинки получить не удалось:
df = df.loc[df['Имя картинки'] != '-']      # Удаляем элементы
df.reset_index(inplace=True, drop = True)   # Обновим индексы

# Создаём Excel xlsx:
filename = folder_4_tables+'/'+'Pics_yandex.xlsx' # Имя файла сохранения xlsx
writer = pd.ExcelWriter(filename, engine='xlsxwriter',
                        options={'strings_to_urls': False})
df.to_excel(writer, sheet_name='Лист', index=False)
# Ширина колонок:
writer.sheets['Лист'].set_column('A:A', 14)       # Имя картинки
writer.sheets['Лист'].set_column('B:B', 40)       # Прямая ссылка
writer.sheets['Лист'].set_column('C:C', 135)      # Ссылка на сайт
# Сохраняем в csv:
writer.save()
df.to_csv(folder_4_tables+'/'+"Pics_yandex.csv", index=False)
# Сохраняем ДФ в пикл:
df.to_pickle(folder_4_tables+'/'+"Pics_yandex.pkl")
print('Сохранено как Pics_yandex')

# ИЗВЛЕКАЕМ ТЕКСТ ИЗ СОХРАНЁННЫХ ИЗОБРАЖЕНИЙ
df = pd.read_csv(folder_4_tables+'/'+'Pics_yandex.csv')
pytesseract.pytesseract.tesseract_cmd = tesseract_path
get_text_full(df, 'df_texted')
print('Извлечение текста из изображений завершено')