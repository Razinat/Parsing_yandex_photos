### Получение текста с фото
from imports import *
from init import *

"""
Для извлечения текста с картинки будет использоваться Tesseract
Tesseract for win 10 here: https://github.com/UB-Mannheim/tesseract/wiki
https://qna.habr.com/q/841085
"""
def get_text(df):
    """ Функция получения текста из изображений """
    print('Извлечение текста из изображений...')
    df['Текст'] = ''                              # Добавляем колонку текст
    os.system(r'nul>texts_photos.txt')            # Очищаем файл текстовый
    pic_names_list = df['Имя картинки'].tolist()
    for i, pic in enumerate(pic_names_list):
        try:
            image = Image.open('Pictures_downloaded/'+pic+'.JPG')
            text = pytesseract.image_to_string(
                image, lang='rus', config='digits') # Извлекаем цифры из текста
            text = re.sub('\s+', ' ', text)         # Удаляем абзацы пустые
            df['Текст'][i] = text
            with open('texts_photos.txt', 'a') as Txt_file:
                Txt_file.write('\n'+pic+'  '+text)  # Записываем текст в txt
        except Exception:
            pass
    print ('Извлечение текста завершено')


def Parse_BINS_Sber():
    """ Парсим BINs Sberbank """
    BINS_Sber = []           # список бинов сбера
    for page in range(1,4):  # 3 страницы парсим
        res = req.get(
            'https://ibankie.com/banks/ru/sberbank/bins?page='+str(page),
            headers = HEADERS)
        html = BeautifulSoup(res.text, 'lxml')
        html_body = html.find_all('td')  # тело с бинами и прочим
        # берем 6 цифр БИНЫ все из текста:
        BINS_Sber.extend(re.findall('\d{6}', str(html_body)))
    return BINS_Sber


def find_SBER(df, BINS_Sber):
    """ Функция поиска наличия реквизитов сбербанка на изображении """
    cases = []
    for BIN in BINS_Sber:  # Получаем регулярку для поика
        cases.append(BIN + '\d{12,14}')  # БИН 4х-Значный + 12 цифр на карте
    for i, Text in enumerate(df['Текст']):
        requisites = []
        for case in cases:  # Ищем в тексте все варианты под Сбер
            sber_requisites = re.findall(case, Text)  # Ищем номера карты Сбера
            if sber_requisites:
                requisites.extend(sber_requisites)
        if not requisites:
            df['Реквезиты Сбер'][i] = '-'
        else:
            df['Реквезиты Сбер'][i] = requisites


def get_text_full(df, name_to_save_docs):
    """Итоговая функция для получения текста и изобр. и сохр. в csv"""
    get_text(df)                              # Получаем текст из изображений
    # Парсим BINs Сбера
    BINS_Sber = Parse_BINS_Sber()
    BINS_Sber[:] = [i[:4] for i in BINS_Sber] # Первые 4 цифры BIN'a
    BINS_Sber = set(BINS_Sber)
    BINS_Sber = list(BINS_Sber)               # Только уник. сочетания 4х цифр
    with open(folder_4_tables +'/BINS_4x_Sber.txt', 'w') as f:  # Запишем в txt
        for item in BINS_Sber:
            f.write("%s\n" % item)
    print ('BINS 4 цифры сбер:\n',BINS_Sber)

    df['Реквезиты Сбер'] = ''          # Добавляем столбец с реквизитами Сбера
    # Ищем реквизиты Сбера. Добавляем в новую колонку дф 'Реквезиты Сбер'
    find_SBER(df, BINS_Sber)

    df.to_csv(folder_4_tables+'/'+name_to_save_docs+'.csv', index = False)
    df.to_excel(folder_4_tables+'/'+name_to_save_docs+'.xlsx', index = False)
    df.to_pickle(folder_4_tables+'/'+name_to_save_docs+'.p')