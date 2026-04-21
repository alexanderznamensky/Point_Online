# Point_Online for Home Assistant.

## Описание

`Point_Online` — кастомная интеграция для Home Assistant, которая позволяет получать данные из сервиса Point_Online и использовать их в автоматизациях, сценариях и интерфейсе Home Assistant.

Интеграция создаёт сенсоры на основе данных с сайта [Point_Online](https://point.online/), обновляет их в Home Assistant и поддерживает настройку через стандартный интерфейс Home Assistant.

## Возможности

- подключение через UI Home Assistant
- поддержка `config_flow`
- поддержка `OptionsFlow`
- обновление данных через `DataUpdateCoordinator`
- создание сенсоров в Home Assistant
- объединение сущностей в одно устройство
- использование данных в автоматизациях, карточках и сценариях

## Установка

### Через HACS

1. Откройте HACS
2. Перейдите в раздел `Integrations`
3. Нажмите на меню в правом верхнем углу
4. Выберите `Custom repositories`
5. Добавьте ссылку на репозиторий с интеграцией `Point_Online`
6. Укажите тип `Integration`
7. Установите интеграцию
8. Перезапустите Home Assistant

### Вручную

1. Скопируйте папку `point_online` в директорию:

```text
custom_components/point_online/
```

2. Убедитесь, что структура файлов выглядит так:

```text
custom_components/
└── point_online/
    ├── __init__.py
    ├── manifest.json
    ├── const.py
    ├── config_flow.py
    ├── coordinator.py
    ├── sensor.py
    ├── strings.json
    └── translations/
```

3. Перезапустите Home Assistant

## Настройка

После установки:

1. Откройте Home Assistant
2. Перейдите в `Настройки` → `Устройства и службы`
3. Нажмите `Добавить интеграцию`
4. Найдите `Point_Online`
5. Введите параметры подключения
6. Завершите настройку

## Параметры

Интеграция может использовать следующие параметры:

- `host` — адрес сервиса, API или личного кабинета
- `username` — логин
- `password` — пароль
- `scan_interval` — интервал обновления данных

## Сущности

После настройки интеграция может создавать следующие сущности:

- сенсоры состояния
- сенсоры баланса
- сенсоры даты или времени последнего обновления
- дополнительные информационные сенсоры с атрибутами

## Пример автоматизации

Пример автоматизации для уведомления при изменении состояния:

```yaml
automation:
  - alias: "Уведомление при изменении состояния Point_Online"
    triggers:
      - trigger: state
        entity_id: sensor.point_online_status
    actions:
      - action: notify.mobile_app
        data:
          message: "Статус Point_Online изменился: {{ states('sensor.point_online_status') }}"
```

## License

MIT
