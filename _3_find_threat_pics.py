## Поиск подозрительных картинок
from imports import *
from init import *

# ДФ от первого парсера яндекса с текстом
# (parsing_ya_joint.ipynb > get_text_photo.ipynb)
df_first_parse = pd.read_pickle(folder_4_tables + '/'+'df_texted.p')
# ДФ Похожих картинок со сбер реквизитами
# (Parse_YA_Similar_img.ipynb > get_text_photo_similar.ipynb):
df_similar = pd.read_pickle(folder_4_tables + '/'+'df_similar_texted.p')
# Объединяем два датафрейма
df = pd.concat([df_first_parse, df_similar])
df.reset_index(drop=True, inplace=True)
df_sber_req = df.loc[df['Реквезиты Сбер'] != '-'].\
    reset_index(drop = True)    # изобр.с реквизитами сбера
df_others = df.loc[df['Реквезиты Сбер'] == '-'].\
    reset_index(drop = True)    # изобр.без реквизитов сбера
# Удалим повторяющиеся реквизиты в одной картинке:
for i in range(len(df_sber_req)):
    df_sber_req['Реквезиты Сбер'][i] = [
        i[0] for i in groupby(df_sber_req['Реквезиты Сбер'][i])]


def resize_c2vimage(image, x, y):
    """ Функция изменения размера cv2 изображения """
    image_base = Image.fromarray(image)       # базовая картинка из cv2 в Image
    image_resized = image_base.resize((x, y), Image.LANCZOS) # меняем размер
    cv2_image_resized = cv2.cvtColor(np.array(image_resized),
                                     cv2.COLOR_RGB2BGR) # преобразуем в cv2
    return cv2_image_resized


def unique_pairs(list_sber_pics, list_other_pics, fl_Only_Sber):
    """ Уникальные пары картинок. Реквизитные с безреквизитными,
    реквизитные между собой """
    pairs = []             # список с уник.парами картинок (напр: 'p1_3 p2_1')
    # Пары между реквизитными и безреквизитными картинками.
    if not fl_Only_Sber:    # Если флаг только сбер реквизиты отсутствует
        for i in range(len(list_sber_pics)):
            for q in range(len(list_other_pics)):
                pairs.append(list_sber_pics[i]+' '+list_other_pics[q])
    # Пары между реквизитными картинками
    for q in range(len(list_sber_pics)):
        for i in range(len(list_sber_pics)-(1+q)):
            pairs.append(list_sber_pics[q]+' '+list_sber_pics[i+q+1])
    return pairs


def image_correlation(pic_name_pairs):
    """ Функция определения схожести изображений """
    corr_list = []                       # список с соответствиями пар картинок
    for i in range(len(pic_name_pairs)):
        pic_names = re.split(' ', pic_name_pairs[i])  # делим пару на 2 элемента
        # Получаем cv2 изображение Numpy array:
        image_1 = cv2.imread(folder_path+'/'+pic_names[0]+'.jpg')
        image_2 = cv2.imread(folder_path+'/'+pic_names[1]+'.jpg')
        # Во избежание ошибок по несоотв.размеров, приводим к одному размеру:
        # Наименьший X и Y размер из двух картинок:
        min_x = min(image_1.shape[0], image_2.shape[0])
        min_y = min(image_1.shape[1], image_2.shape[1])
        # Меняем размер изображений:
        image_1 = resize_c2vimage(image_1, min_x, min_y)
        image_2 = resize_c2vimage(image_2, min_x, min_y)
        # Соответствие картинок
        corr = (cv2.matchTemplate(image_1, image_2, cv2.TM_CCOEFF_NORMED)[0][0])
        corr_list.append(corr)
    return corr_list

# Получаем пары картинок для поиска схожих
pic_name_pairs = unique_pairs(df_sber_req['Имя картинки'].tolist(),
                              df_others['Имя картинки'].tolist(), True)
print ('Количество пар картинок:', len(pic_name_pairs))

# Расчёт корреляций
if Do_corrs:
    corrs = image_correlation(pic_name_pairs)
    # Сохраним корреляции
    with open("corrs.txt", "wb") as fp:  # Pickling
        pickle.dump(corrs, fp)
if not Do_corrs:
    with open("corrs.txt", "rb") as fp:    # Unpickling
        corrs = pickle.load(fp)


def similar_images(corrs, threshold_down, threshold_up, pic_name_pairs):
    """ Функция определения похожих изображений с различными реквизитами """
    # списки с индексами, значениями корреляций, похожими изображениями:
    indices, big_corrs, similar_pics = [], [], []
    for i in range(len(corrs)):  # По всем коррелациям пар картинок:
        # Если величина корреляции больше порога, добавляем:
        if threshold_down < corrs[i] < threshold_up:
            indices.append(corrs.index(corrs[i],i))
            big_corrs.append(corrs[i])  # Добавляем корреляцию в список
            # добавляем пару в список похожих:
            similar_pics.append(pic_name_pairs[corrs.index(corrs[i],i)])

    # Убираем из списка похожих картинок, если реквизиты указаны одинаковые:
    similar_pics_ = similar_pics.copy()
    for i, pair in enumerate(similar_pics):  # по всем похожим картинкам:
        pair_ = (re.split(' ', pair))        # делим пару на 2 элемента
        try:
            # Сберовские реквизиты первой и второй картинки из пары:
            reqs_first = df_sber_req.loc[
                df_sber_req['Имя картинки'] == pair_[0], 'Реквезиты Сбер'].iloc[
                0]
            reqs_second = df_sber_req.loc[
                df_sber_req['Имя картинки'] == pair_[1], 'Реквезиты Сбер'].iloc[
                0]
            # Если реквизиты совпали, удаляем пару из анализа дальнейшего
            if reqs_first == reqs_second:
                similar_pics_.remove(pair)  # удаляем пару
                print(f'Пара {pair} '
                      f'удалена из-за одинаковых реквизитов или прямых ссылок')
        except Exception:
            similar_pics_.remove(
                pair)  # удаляем пару, если возникло какое-то исключение
            print(f'Пара {pair} удалена по Exception')
            pass
    return indices, big_corrs, similar_pics_

indices, big_corrs, similar_pics = similar_images(corrs,
                                                  0.7,
                                                  0.995,
                                                  pic_name_pairs)
print ('Похожие картинки с разными реквизитами: \n', similar_pics)


def unique_pics_threats():
    """ Ищем уникальные картинки в парах с угрозой """
    unique_similar_pics = []
    for pair in similar_pics:
        unique_similar_pics.append(
            re.split(' ', pair))  # Сплитим пары на отдельные картинки
    unique_similar_pics_ = []
    for iter in range(len(unique_similar_pics)):  # Уникальные картинки из пар
        for q in range(len(unique_similar_pics[iter])):
            unique_similar_pics_.append(unique_similar_pics[iter][q])
    unique_similar_pics_ = set(unique_similar_pics_)
    unique_similar_pics_ = list(unique_similar_pics_)
    return unique_similar_pics_


unique_pics_threats()


def save_threats():
    """ Функция сохранения подозрительных картинок и файла эксель с ними """
    unique_threat_pics = unique_pics_threats()  # выделяем уникальные картинки
    for pic in unique_threat_pics:  # по каждой уникальной картинке
        with open(folder_for_threat + pic + '.jpg', 'wb') as f:
            image = Image.open(folder_path + pic + '.jpg').convert('RGB')
            image.save(f, "JPEG", quality=100)  # сохраняем картинку

    # Создаём новый ДФ с угрозами:
    df_threat = df_sber_req.copy()
    df_threat['Пары'] = ''
    # Оставляем только те картинки, которые есть в списке уникальных:
    df_threat = df_threat[df_threat['Имя картинки'].isin(unique_threat_pics)]
    df_threat.reset_index(drop=True, inplace=True)
    for i in range(len(df_threat)):
        pairs = []  # список имеющихся уникальных пар для картинки
        for pair in similar_pics:
            if df_threat['Имя картинки'][i] in pair: # если картинка есть в паре
                pairs.append(pair)          # добавляем уникальную пару
            df_threat['Пары'][i] = (pairs)  # уникальные пары к картинке
    return df_threat


if not os.path.isdir(folder_for_threat):
     os.mkdir(folder_for_threat)   # Каталог для сохр.картинок с фальсификациями
# Сохраняем уникальные картинки в каталог, получаем датафрейм с ними
df_threat = save_threats()
df_threat.head(10)
# Создаём Excel xlsx:
writer = pd.ExcelWriter(folder_for_threat+'Pics_threat.xlsx',
                        engine='xlsxwriter')
df_threat.to_excel(writer, sheet_name='Лист', index=False)
# Ширина колонок:
writer.sheets['Лист'].set_column('A:A', 12)       # Имя картинки
writer.sheets['Лист'].set_column('B:B', 30)       # Прямая ссылка
writer.sheets['Лист'].set_column('C:C', 30)       # Ссылка на сайт
writer.sheets['Лист'].set_column('D:D', 30)       # Текст с картинки
writer.sheets['Лист'].set_column('E:E', 25)       # Реквизиты сбера
writer.sheets['Лист'].set_column('F:F', 60)       # Пары к картинке
# Сохраняем:
writer.save()
df_threat.to_csv(folder_for_threat+'Pics_threat.csv', index=False)
print (f'Картинки потенциально фейковые сохранены в каталог '
       f'{folder_for_threat}. Эксель сохранён как Pics_threat')