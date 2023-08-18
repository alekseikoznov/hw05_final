# Проект Yatube

## Описание проекта:

Проект "Yatube" представляет собой представляет социальную сеть для публикации личных дневников.<br>
Соцсеть реализована на фреймворке Django.

Пользователи могут вести свои микроблоги, подписываться на интересных авторов и комментировать их публикации.

## Технологии проекта:

- Python 3.7
- Django 2.2
- Pytest 6.2

## Установка:

Для установки проекта на локальной машине необходимо:

1. Клонировать репозиторий и перейти в него в командной строке:
```
git clone git@github.com:alekseikoznov/yatube.git
```
```
cd yatube
```
2. Cоздать и активировать виртуальное окружение:
```
python -m venv venv
```
* Если у вас Linux/macOS
    ```
    source venv/bin/activate
    ```
* Если у вас Windows
    ```
    source venv/scripts/activate
    ```
3. Обновить менеджер пакетов pip:
```
python -m pip install --upgrade pip
```
4. Установить зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```
5. В папке с файлом manage.py выполните миграции:
```
python manage.py migrate
```
6. В папке с файлом manage.py запустите локальный сервер:
```
python manage.py runserver
```
