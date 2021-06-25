# Парсинг похожих картинок в яндексе
from GetText import *
from imports import *
from init import *
warnings.filterwarnings("ignore")

df = pd.read_csv(folder_4_tables + '/' + 'df_texted.csv')
df = df.loc[df['Реквезиты Сбер'] != '-']  # ищем, где есть реквизиты сбера
df.reset_index(inplace = True)


def make_hyperlink(link, text):
    """ Функция создания гиперссылок для документа в Excel """
    return '=HYPERLINK("%s", "%s")'%(link, text)


def get_links(pics,yandex_search_link):
    """ Забираем ссылки из pics """
    links, links_to_site, links_yandex = [], [], []
    for i, pic in enumerate(pics):
        # Ищем сайт с картинкой (вкладку с ней)
        link_to_site = re.findall('(?<=","url":").*?(?=",)', str(pic.get_text))
        if link_to_site:
            links_to_site.append(link_to_site[0])
            # Ищем прямую ссылку, только если нашли сайт c картинкой
            #(иначе может быть косяк, когда одна ссылка есть, а другой нет)
            # Поиск от начала совпадения до конца. Берем прямую ссылку на картинку:
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


def parse_for_similar_pics(link):
    """ Ищем ссылку на похожие картинки.
    Через Selenium, т.к ссылка выдаётся через Java скрипт """
    browser = webdriver.Firefox(executable_path=path_driver)
    browser.get(link)  # открываем браузер - переходим по ссылке
    # Кликаем на кнопку просмотра похожих изображений, закрываем вспл. окно,
    # (если этого не сделать, ссылка href на поиск похожих картинок не появится)
    time.sleep(2)  # сон после открытия страницы
    browser.find_element_by_class_name(
        'MMViewerButtons-SearchByImage').click()  # клик кнопки 'показать похожие'
    time.sleep(1)  # сон после клика кнопки 'показать похожие'
    browser.find_element_by_class_name(
        'MMUnauthPopup-CloseIcon').click()  # клик кнопки 'закрыть'
    time.sleep(1)  # сон после открытия всплывающего откна
    # Снова кликаем кнопку, чтобы перейти по ссылке.
    # (ссылка недействителна при переходе не с кнопки). Она динамически меняется
    browser.find_element_by_class_name(
        'MMViewerButtons-SearchByImage').click() # клик 'показать похожие'
    # Получаем ссылку текущей страницы (первичная ссылка на 'похожие картинки'):
    link_similar_perv = browser.current_url
    browser.close()  # закрываем браузер
    # Парсим первичную ссылку на 'похожие картинки' > ссылка под "parse"
    res = req.get(link_similar_perv, headers=HEADERS)
    html = BeautifulSoup(res.text, 'lxml')
    body = html.find('body', class_='b-page__body')
    div = body.find('div', class_='page-layout_page_search-by-image')
    c = 'button2 button2_theme_normal button2_size_n button2_type_link' + \
        ' button2_width_max button2_tone_default button2_view_default link' + \
        ' link_theme_normal link_ajax_yes cbir-similar__more i-bem',
    body_for_pictures = div.find('a', class_=c, href=True)
    return ('https://yandex.ru' + body_for_pictures['href'])


def save_pics(links):
    """ Сохраняем картинки по ссылкам """
    # 'C:/Users/alexk/Documents/'+ 'Parsing photos ya/Pictures_downloaded
    i = 0
    fl_saved = []  # Флаг - "Картинка сохранена". Имя
    for url in links:
        i += 1  # Порядковый номер картинки на странице
        filename = 'Similar_' + name_similar_pic + '_n' + str(
            i) + '.jpg'  # Имя файла сохранения
        # Попытки соединения с сервером картинки:
        try:
            req.post(url, timeout=10)  # Запрос к картинке
            try:
                image_content = req.get(url, timeout=10).content
            except Exception as e:
                print(f"Невозможно загрузить картинку {url} — {e}")
            try:
                image_file = io.BytesIO(image_content)
                image = Image.open(image_file).convert('RGB')
                # Полный путь к файлу картинки
                file_path = folder_path + '/' + filename
                with open(file_path, 'wb') as f:
                    image.save(f, "JPEG",
                               quality=50)  # Сохр.картинку, уменьшаем кач-во
                    print(filename[:-4], url, f"Сохранено как {filename}")
                    fl_saved.append(filename[:-4])
            except Exception as e:
                print(filename[:-4], url, f"Ошибка сохранения — {e}")
                fl_saved.append('-')
        # except req.exceptions.ConnectionError as e:
        except Exception:  # Если таймаут,пропускаем картинку
            print(filename[:-4], url, 'Нет ответа от сервера')
            fl_saved.append('-')
    return fl_saved

list_links_to_pics, list_links_to_websites, \
fls_saved, list_links_yandex = [], [], [], []

req_num = 0
passed = 0                                # Кол-во пропусков

for i, link in enumerate(df['Ссылка на яндекс в поиске']):
    try:
        name_similar_pic = df['Имя картинки'][i] # Картинка, к котор. ищем похож
        req_num += 1                             # Порядковый номер запроса
        # Получаем ссылку на похожие картинки:
        link_for_parse = parse_for_similar_pics(link)
        # Получаем ссылку на картинки и ссылки на сайт:
        links_pic,links_to_website, links_yandex = get_links(
            parse(link_for_parse)[0], parse(link_for_parse)[1])
        fl_saved = save_pics(links_pic[:n_similar])        # Сохраняем картинку
        list_links_to_pics.extend(links_pic[:n_similar])   # прямые link pic
        list_links_to_websites.extend(links_to_website[:n_similar])    # сайт
        list_links_yandex.extend(links_yandex[:n_similar])      # похож. pics
        fls_saved.extend(fl_saved[:n_similar])      # Имя сохраненной картинки
        passed = 0
        time.sleep(5)          # Пауза между страницами, чтобы не откл.запросы
    except Exception:
        print('passed')        # Если картинка не открылась, пропускаем итерацию
        passed += 1
    if i%10 == 0:              # Раз в несколько ссылок засыпаем
        time.sleep(10)
    if passed > 16:
        i_stop = i
        print(f'Прервано в связи с отклонением сервера на {i_stop} элементе')
        break

# Делаем гиперссылки для кликабельности в документе Excel:
hyperlink_pics, hyperlink_websites = [], []
for link in list_links_to_pics:
    hyperlink_pics.append(make_hyperlink(link, str(link)))
for link in list_links_to_websites:
    hyperlink_websites.append(make_hyperlink(link, str(link)))

# Создаём датафрейм из полученных списков:
df = pd.DataFrame()
df['Имя картинки'] = fls_saved
df['Прямая ссылка'] = hyperlink_pics
df['Ссылка на сайт'] = hyperlink_websites
df['Ссылка на яндекс в поиске'] = list_links_yandex  # передаём без гиперссылки

# Удаляем строки, где картинки получить не удалось:
df = df.loc[df['Имя картинки'] != '-']
df.reset_index(inplace=True, drop = True)   # Обновим индексы

df.to_csv(folder_4_tables+'/'+'Pics_yandex_similar.csv', index = False)
df.to_pickle(folder_4_tables+'/'+"Pics_yandex.pkl")
df.to_excel(folder_4_tables+'/'+'Pics_yandex_similar.xlsx', index = False)
print ('Сохранено как Pics_yandex_similar')

# ИЗВЛЕКАЕМ ТЕКСТ ИЗ СОХРАНЁННЫХ ИЗОБРАЖЕНИЙ
df = pd.read_csv(folder_4_tables+'/'+'Pics_yandex_similar.csv')
pytesseract.pytesseract.tesseract_cmd = tesseract_path
get_text_full(df, 'df_similar_texted')