import requests
import datetime
import os
import json
import tqdm

# Функция чтения токена и айди из файла
def get_token_id(file_name):
    with open(os.path.join(os.getcwd(), file_name), 'r') as token_file:
        token = token_file.readline().strip()
        id_one = token_file.readline().strip()
    return [token, id_one]
# Максимального размера фото
def find_max_size(serch):
    max_dpi = 0
    need_element = 0
    for i in range(len(serch)):
        file_dpi = serch[i].get('width') * serch[i].get('height')
        if file_dpi > max_dpi:
            max_dpi = file_dpi
            need_element = i
    return serch[need_element].get('url'), serch[need_element].get('type')

# Функция преобразует дату загрузки фото в привычный формат
def time_convert(time_unix):
    time_bc = datetime.datetime.fromtimestamp(time_unix)
    str_time = time_bc.strftime('%Y-%m-%d time %H-%M-%S')
    return str_time

class VK:
    # Получение основных парамметров в ВК
    def __init__(self, access_token, user_id, version='5.199'):
        self.token = access_token
        self.id = user_id
        self.version = version
        self.start_params = {'access_token': self.token, 'v': self.version}
        self.json, self.export_dict = self._sort_info()

    # Метод получения доступа к фото
    def _photo_get_inf(self):
        url = 'https://dev.vk.com/ru/method/photos.get'
        params = {'ower_id':self.id,
                  'album_id': 'profile',
                  'rev': 0,
                  'extended': 1,
                  'photo_size': 1
                  }
        photo_info = requests.get(url, params={**self.start_params, **params}).json()['response']
        return photo_info['count'], photo_info['items']

    # Словарь с параметрами фото
    def _get_logs (self):
        photo_count, photo_items = self._photo_get_inf()
        result = {}
        for j in range (photo_count):
            likes_count = photo_items[j]['likes']['count']
            url_downlod, picture_size = find_max_size(photo_items[j]['sizes'])
            time_warp = time_convert(photo_items[j]['date'])
            new_value = result.get(likes_count, [])
            new_value.append({'likes_count': likes_count,
                              'add_name': time_warp,
                              'url_picture': url_downlod,
                              'size': picture_size})
            result[likes_count] = new_value
        return result
# создание Словаря с параметрами фото и списка json для выгрузки
    def _sort_info(self):
        json_list = []
        sorted_dict = {}
        picture_dict = self._get_logs_only()
        counter = 0
        for elem in picture_dict.keys():
            for value in picture_dict[elem]:
                if len(picture_dict[elem]) == 1:
                    file_name = f'{value["likes_count"]}.jpeg'
                else:
                    file_name = f'{value["likes_count"]} {value["add_name"]}.jpeg'
                json_list.append({'file name': file_name, 'size': value["size"]})
                if value["likes_count"] == 0:
                    sorted_dict[file_name] = picture_dict[elem][counter]['url_picture']
                    counter += 1
                else:
                    sorted_dict[file_name] = picture_dict[elem][0]['url_picture']
        return json_list, sorted_dict

class YandexApi:
    # получение основняых параметров для загрузки на яндекс диск
    def __init__(self, folder_name, token_list, num=5):
        self.token = token_list[0]
        self.added_files_num = num
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
#получения ссылки для загрузки фотографий на Я-диск
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
        """Метод загрузки фотографий на Я-диск"""
        files_in_folder = self._in_folder(self.folder)
        copy_counter = 0
        for key, i in zip(dict_files.keys(), tqdm(range(self.added_files_num))):
            if copy_counter < self.added_files_num:
                if key not in files_in_folder:
                    params = {'path': f'{self.folder}/{key}',
                              'url': dict_files[key],
                              'overwrite': 'false'}
                    requests.post(self.url, headers=self.headers, params=params)
                    copy_counter += 1
                else:
                    print(f'Внимание:Файл {key} уже существует')
            else:
                break
        print(f'\nЗапрос завершен, новых файлов скопировано (по умолчанию: 5): {copy_counter}'
              f'\nВсего файлов в исходном альбоме VK: {len(dict_files)}')

if __name__ == '__main__':

    tokenVK = 'VK_TOKEN.txt'  # токен и id доступа хранятся в файле (построчно)
    tokenYandex = 'Ya_TOKEN.txt'  # хранится только токен яндекс диска

    my_VK = VK(get_token_id(tokenVK))  # Получение JSON списка с информацией о фотографииях

    with open('my_VK_photo.json', 'w') as outfile:  # Сохранение JSON списка ф файл my_VK_photo.json
        json.dump(my_VK.json, outfile)

    # Создаем экземпляр класса Yandex с параметрами: "Имя папки", "Токен" и количество скачиваемых файлов
    my_yandex = YandexApi('VK photo copies', get_token_id(tokenYandex), 5)
    my_yandex.create_copy(my_VK.export_dict)  # Вызываем метод create_copy для копирования фотографий с VK на Я-диск