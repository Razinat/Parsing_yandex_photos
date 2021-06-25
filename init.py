# Добавляем хэдэрс, чтобы запросы не отклонялись
HEADERS = {
    'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'user-agent':'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.5)'
                 ' Gecko/20091102 Firefox/3.5.5 (.NET CLR 3.5.30729)'
}

folder_path = 'Pictures_downloaded'  # папка для сохранения картинок
folder_4_tables = 'docs'             # папка для сохр.табличек
folder_for_threat = 'Threat_pics/'   # каталог для сохр. потенц.фальсиф.картинок

n_similar = 5   # Кол-во похожих картинок к картинке для сохранения  в выборку
num_pages_to_parse = 1         # сколько страниц с картинками парсим по запросу

tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe" # exe тессеракт
path_driver = r'C:\Users\larav\PycharmProjects\Parsing_yandex' \
              r'\selenium_driver\geckodriver.exe' # драйвер Firefox for selenium

Do_corrs = True    # рассчитывать корреляции изображений