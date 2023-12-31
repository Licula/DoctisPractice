# Практика Doctis

## Описание

В процессе выполнения практики было реализовано ПО для анализа КТГ плода. Совпадение анализа врача и программы составляет 80%. При анализе КТГ использовалась бальная система оценки Фишера.

## Запуск

Для запуска программы необходимо:
1. клонировать git-репозиторий ```git clone https://github.com/Licula/DoctisPractice.git```
2. находясь в корневом каталоге репозитория, создать виртуальное окружение и установить необходимые зависимости ```make build```
3. активировать виртуальное окружение ```source venv/bin/activate```
4. запустить программу ```make run``` или запустить вручную ```python3 main.py -d ./ctg_files -p 8```

команда ```make visualize``` запускает отрисовку графиков

### Параметры запуска

**-d** - путь к директории с файлами данных КТГ

**-p** - количество процессов-обработчиков

**-visualize** - флаг, если установлен запускается отрисовка графиков и их сохранение в папке **./graphs**

### Результат работы программы

* Среднее время обработки одного файла
* Процент совпадения результата работы программы и врача
* файл **comparision.json** с более подробным результатом работы, показывающий совпадение по файлам
* log-file **ctg.log**


### Тестирование происходило под macOS