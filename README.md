

# FOODGRAM—  это социальная сеть для обмена рецептами между любителя вкусно поесть. 

![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white) ![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E) ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white) ![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray) ![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white) ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white) ![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white) ![GitHub Actions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=githubactions&logoColor=white)

## Описание проекта
Проект написан в рамках учебного курса. 
Данный проект для тех, кто умеет хорошо готовить и вкусно поесть.
Пользователи могут регистрироваться, создавать рецепты, читать рецепты, подписываться на авторов рецептов, создавать и скачитьвать списки продуктов с их колличеством для дальнейшей покупки продуктов и приготовления понравивщихся блюд.

## Технологии

 - Python 3.9
 - Django 3.2.3
 - Django REST framework 3.12.4
 - JavaScript
 - Nginx
 - gunicorn
 - docker
 - PstgreSQL

## Запуск из оконтейнеров на Docker hub:

Для запуска необходимо на создать папку с названием проекта: `foodgram-project-react`
sudo mkdir foodgram-project-react
перейти в нее:
sudo cd foodgram-project-react

В папку проекта сохраняем файл: `docker-compose.production.yml`

Запускаем его: sudo docker compose -f docker-compose.production.yml up

Выполнится скачивание, распаковка образов, создание и запуск контейнеров.


## Запуск проекта из исходников GitHub

Клонируем себе репозиторий: git clone git@github.com:prz13/foodgram-project-react.git

Выполняем запуск: sudo docker compose -f docker-compose.yml up

## После запуска: 

После запуска необходимо выполнить сбор статики, выполнить миграции.  

Выполнить поочередно:

Создайте и примените миграции
sudo docker compose -f docker-compose.production.yml exec backend python manage.py makemigrations recipes
sudo docker compose -f docker-compose.production.yml exec backend python manage.py makemigrations users
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate

Выполните сборку и копирование статики проекта
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /collected_static

Выполните копирование базы данных ингирдиентов из базы данных в проект
sudo docker compose -f docker-compose.production.yml exec backend python manage.py load_ingredients


## Остановка проекта в консоле: 
Зажав на клавиатуре Ctrl+С
Или в другом окне терминала выполнить: sudo docker compose -f docker-compose.yml down

Проект временно доступен по адресу: foodbook.myftp.biz
