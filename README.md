

# FOODGRAM—  это социальная сеть для обмена рецептами. 

![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white) ![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E) ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white) ![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray) ![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white) ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white) ![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white) ![GitHub Actions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=githubactions&logoColor=white)

## Описание проекта
Проект написан в рамках учебного курса.
Пользователи могут регистрироваться, создавать рецепты, читать рецепты, подписываться на авторов рецептов, создавать и скачитьвать списки продуктов с их колличеством для дальнейшего приготовления выбраных блюд.

## Технологии

 - Python 3.9
 - Django 3.2.3
 - Django REST framework 3.12.4
 - JavaScript
 - Nginx
 - gunicorn
 - docker
 - PstgreSQL

## Запуск  из оконтейнеров с Docker hub

Для запуска необходимо на создать папку с названием проекта: `foodgram` и перейти в нее:

mkdir foodgram
cd foodgram


В папку проекта сохраняем файл: `docker-compose.production.yml`

Запускаем его: sudo docker compose -f docker-compose.production.yml up


Выполнится скачивание, распаковка образов, создание и запуск контейнеров.


## Запуск проекта из исходников GitHub

Клонируем себе репозиторий: git clone git@github.com:prz13/foodgram-project-react.git

Выполняем запуск: sudo docker compose -f docker-compose.yml up

## После запуска: 

После запуска необходимо выполнить сбор статики, выполнить миграции.  

Выполнить поочередно:
sudo docker compose -f [имя-файла-docker-compose.yml] exec backend python manage.py migrate

sudo docker compose -f [имя-файла-docker-compose.yml] exec backend python manage.py collectstatic

sudo docker compose -f [имя-файла-docker-compose.yml] exec backend cp -r /app/collected_static/. /static/static/


Проект будет доступен: http://localhost:8000/


## Остановка проекта в консоле: Ctrl+С
Или в другом окне терминала выполнить: sudo docker compose -f docker-compose.yml down
