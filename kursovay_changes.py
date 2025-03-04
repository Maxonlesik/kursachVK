import requests
import datetime
import os
import json
import tqdm


# Функция чтения токена и айди из файла
def get_token_id(file_name):
    with open(os.path.join(os.getcwd(), file_name), 'r') as token_file:
        token = token_file.readline().strip()
        id = token_file.readline().strip()
    return [token, id]


# Максимального размера фото
def find_max_dpi(dict_in_search):
    max_dpi = 0
    for j in range(len(dict_in_search)):
        file_dpi = dict_in_search[j].get('width') * dict_in_search[j].get('height')
        if file_dpi > max_dpi:
            max_dpi = file_dpi
            need_elem = j
    return dict_in_search[need_elem].get('url'), dict_in_search[need_elem].get('type')


# Функция преобразует дату загрузки фото в привычный формат
def time_convert(time_unix):
    time_bc = datetime.datetime.fromtimestamp(time_unix)
    str_time = time_bc.strftime('%Y-%m-%d time %H-%M-%S')
    return str_time


class VK_request:
    # Получение основных парамметров в ВК
    def __init__(self, token_list, version='5.131'):
        self.token = token_list[0]
        self.id = token_list[1]
        self.version = version
        self.start_params = {'access_token': self.token, 'v': self.version}
        self.json, self.export_dict = self._sort_info()

    # Метод получения доступа к фото
    def _get_photo_info(self):
        url = 'https://api.vk.com/method/photos.get'
        params = {'owner_id': self.id,
                  'album_id': 'profile',
                  'photo_sizes': 1,
                  'extended': 1}
        photo_info = requests.get(url, params={**self.start_params, **params}).json()['response']
        return photo_info['count'], photo_info['items']

    # Словарь с параметрами фото
    def _get_logs_only(self):
        photo_count, photo_items = self._get_photo_info()
        result = {}
        for i in range(photo_count):
            likes_count = photo_items[i]['likes']['count']
            url_download, picture_size = find_max_dpi(photo_items[i]['sizes'])
            time_warp = time_convert(photo_items[i]['date'])
            new_value = result.get(likes_count, [])
            new_value.append({'add_name': time_warp,
                              'url_picture': url_download,
                              'size': picture_size})
            result[likes_count] = new_value
        return result

    # создание Словаря с параметрами фото и списка json для выгрузки
    def _sort_info(self):
        json_list = []
        sorted_dict = {}
        picture_dict = self._get_logs_only()
        for elem in picture_dict.keys():
            for value in picture_dict[elem]:
                if len(picture_dict[elem]) == 1:
                    file_name = f'{elem}.jpeg'
                else:
                    file_name = f'{elem} {value["add_name"]}.jpeg'
                json_list.append({'file name': file_name, 'size': value["size"]})
                sorted_dict[file_name] = picture_dict[elem][0]['url_picture']
        return json_list, sorted_dict

class Yandex:
    # получение основняых параметров для загрузки на яндекс диск
    def __init__(self, folder_name, token_list):
        self.token = token_list[0]
        self.url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        self.headers = {'Authorization': self.token}
        self.folder = self._create_folder(folder_name)

    # создание папки на яндекс диске и загрузки фото
    def _create_folder(self, folder_name):
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        params = {'path': folder_name}
        if requests.get(url, headers=self.headers, params=params).status_code != 200:
            requests.put(url, headers=self.headers, params=params)
            print(f'\nПапка {folder_name} успешно создана в корневом каталоге Яндекс диска\n')
        else:
            print(f'\nПапка {folder_name} уже существует. Файлы с одинаковыми именами не будут скопированы\n')
        return folder_name

    # получения ссылки для загрузки фотографий на Я-диск
    def _in_folder(self, folder_name):
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        params = {'path': folder_name}
        resource = requests.get(url, headers=self.headers, params=params).json()['_embedded']['items']
        in_folder_list = []
        for elem in resource:
            in_folder_list.append(elem['name'])
        return in_folder_list

    # Загрузка фото на яндекс диск
    def create_copy(self, dict_files):
        files_in_folder = self._in_folder(self.folder)
        added_files_num = 0
        for key in dict_files.keys():
            if key not in files_in_folder:
                params = {'path': f'{self.folder}/{key}',
                          'url': dict_files[key],
                          'overwrite': 'false'}
                requests.post(self.url, headers=self.headers, params=params)
                print(f'Файл {key} успешно добавлен')
                added_files_num += 1
            else:
                print(f'Копирование отменено:Файл {key} уже существует')
        print(f'\nЗапрос завершен, новых файлов добавлено: {added_files_num}')


    tokenVK = 'tokenVKuser2.txt'  # токен и id доступа хранятся в файле
    tokenYandex = 'tokenYandex.txt'  # хранится только токен яндекс диска

    my_VK = VK_request(get_token_id(tokenVK))
    print(my_VK.json)

    my_yandex = Yandex('VK photo copies', get_token_id(tokenYandex))
    my_yandex.create_copy(my_VK.export_dict)
