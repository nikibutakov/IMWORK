# Инструкция по запуску и использованию тестов ImWork Bot

## 📋 Содержание
1. [Установка зависимостей](#установка-зависимостей)
2. [Команды для запуска тестов](#команды-для-запуска-тестов)
3. [Структура тестовых файлов](#структура-тестовых-файлов)
4. [Как читать вывод pytest](#как-читать-вывод-pytest)
5. [Авто-фиксы кода](#авто-фиксы-кода)

---

## Установка зависимостей

```bash
# Перейдите в директорию проекта
cd /workspace/imwork_bot

# Установите зависимости для тестирования
pip install -r tests/requirements-test.txt

# Или добавьте к основным зависимостям:
pip install pytest==8.3.4 pytest-asyncio==0.24.0 pytest-mock==3.14.0 aiosqlite==0.20.0
```

---

## Команды для запуска тестов

### Запуск всех тестов
```bash
pytest tests/ -v
```

### Последовательный запуск по файлам (рекомендуется)

#### 1. Тесты онбординга
```bash
pytest tests/test_onboarding.py -v --tb=short
```

#### 2. Тесты студента (поиск вакансий)
```bash
pytest tests/test_student_flow.py -v --tb=short
```

#### 3. Тесты работодателя
```bash
pytest tests/test_employer_flow.py -v --tb=short
```

#### 4. Тесты карьерного центра
```bash
pytest tests/test_career_center.py -v --tb=short
```

#### 5. Тесты граничных случаев
```bash
pytest tests/test_edge_cases.py -v --tb=short
```

### Запуск по маркерам (категориям)

```bash
# Только тесты онбординга
pytest tests/ -v -m onboarding

# Только тесты студентов
pytest tests/ -v -m student

# Только тесты работодателей
pytest tests/ -v -m employer

# Только тесты карьерного центра
pytest tests/ -v -m career_center

# Только edge cases
pytest tests/ -v -m edge_cases

# Пропущенные тесты (MVP заглушки)
pytest tests/ -v -m "skip_mvp or skip"
```

### Запуск с отчетом о покрытии
```bash
# Требуется установить: pip install pytest-cov
pytest tests/ -v --cov=handlers --cov=models --cov-report=html
```

### Запуск конкретного теста
```bash
pytest tests/test_onboarding.py::test_start_new_user_shows_role_selection -v
```

### Запуск до первой ошибки
```bash
pytest tests/ -x -v
```

---

## Структура тестовых файлов

```
tests/
├── conftest.py              # Фикстуры и конфигурация pytest
├── requirements-test.txt    # Зависимости для тестов
├── test_onboarding.py       # Сценарий 1: Онбординг пользователей
├── test_student_flow.py     # Сценарий 2: Поиск стажировки
├── test_employer_flow.py    # Сценарий 3: Создание вакансий
├── test_career_center.py    # Сценарий 4: Карьерный центр
└── test_edge_cases.py       # Сценарий 5: Граничные случаи
```

---

## Как читать вывод pytest

### Пример успешного теста
```
tests/test_onboarding.py::test_start_new_user_shows_role_selection PASSED [  2%]
```

### Пример проваленного теста
```
tests/test_onboarding.py::test_start_new_user_shows_role_selection FAILED [  2%]

=================================== FAILURES ===================================
__________________ test_start_new_user_shows_role_selection ___________________

dp_with_handlers = <Dispatcher ...>, mock_message = <Message ...>
db_session = <AsyncSession ...>, bot_checker = <BotCallChecker ...>

    @pytest.mark.asyncio
    async def test_start_new_user_shows_role_selection(...):
        ...
>       bot_checker.assert_send_message_called("Добро пожаловать")
E       AssertionError: send_message не был вызван

tests/test_onboarding.py:45: AssertionError
```

### Какие строки копировать для анализа

При провале теста скопируйте следующие строки:

1. **Название теста** (первая строка FAILURE):
   ```
   tests/test_onboarding.py::test_start_new_user_shows_role_selection FAILED
   ```

2. **Сообщение об ошибке** (строки после `E       `):
   ```
   E       AssertionError: send_message не был вызван
   ```

3. **Место ошибки** (строка с `>`):
   ```
   >       bot_checker.assert_send_message_called("Добро пожаловать")
   ```

4. **Полный traceback** (если нужен детальный анализ):
   ```
   tests/test_onboarding.py:45: AssertionError
   ```

### Формат для отправки на авто-фикс

```
ФАЙЛ: tests/test_onboarding.py
ТЕСТ: test_start_new_user_shows_role_selection
ОШИБКА: AssertionError: send_message не был вызван
СТРОКА: 45
ОЖИДАНИЕ: bot.send_message должен быть вызван с текстом "Добро пожаловать в ImWork Bot"
```

---

## Авто-фиксы кода

### Когда требуется авто-фикс

1. **Тест упал из-за изменения текста в хендлере**
   - Скопируйте ошибку
   - Нейросеть обновит ожидаемый текст в тесте

2. **Тест упал из-за отсутствия хендлера**
   - Помечается как `pytest.skip()`
   - Нейросерь создаст заглушку хендлера

3. **Тест упал из-за изменения структуры БД**
   - Обновите модель в `models.py`
   - Запустите тесты снова

### Процесс авто-фикса

1. Запустите тесты:
   ```bash
   pytest tests/test_onboarding.py -v --tb=short 2>&1 | tee test_output.log
   ```

2. Отправьте вывод нейросети с запросом:
   ```
   Проанализируй ошибки тестов и предложи исправления кода.
   Выведи полный код исправленных файлов.
   ```

3. Примените предложенные исправления

4. Перезапустите тесты для проверки

---

## Маркеры для пропуска тестов

### MVP заглушки
```python
@pytest.mark.skip(reason="Forum MVP: mocked")
async def test_forum_not_implemented():
    ...

@pytest.mark.skip(reason="Not implemented yet")
async def test_payment_integration():
    ...
```

### Тесты-спецификации
Эти тесты описывают требуемое поведение, но функция еще не реализована:
```python
@pytest.mark.skip(reason="Role-based access control not implemented yet")
async def test_student_cannot_access_employer_functions():
    ...
```

---

## Добавление новых тестов

### Шаблон нового теста

```python
@pytest.mark.asyncio
@pytest.mark.<category>  # onboarding, student, employer, career_center, edge_cases
async def test_<description>(
    dp_with_handlers, mock_callback_query, db_session, bot_checker, mock_bot
):
    """
    TEST: Краткое описание сценария из ТЗ.
    
    Сценарий:
    1. Шаг 1
    2. Шаг 2
    3. Ожидаемый результат
    """
    from handlers.<module> import <handler_function>
    
    # Arrange: подготовка данных
    ...
    
    # Act: вызов хендлера
    await <handler_function>(mock_callback_query, db_session)
    
    # Assert: проверка результатов
    bot_checker.assert_edit_message_text_called("ожидаемый текст")
```

---

## Частые проблемы и решения

### Ошибка: `pytest_asyncio is not installed`
```bash
pip install pytest-asyncio==0.24.0
```

### Ошибка: `ModuleNotFoundError: No module named 'models'`
Убедитесь что запускаете из директории проекта:
```bash
cd /workspace/imwork_bot
pytest tests/ -v
```

### Ошибка: `sqlite3.OperationalError: no such table`
Каждый тест получает чистую БД в памяти. Проверьте что:
- Фикстура `db_session` используется
- Таблицы создаются через `Base.metadata.create_all`

### Тесты выполняются слишком долго
Запускайте по одному файлу:
```bash
pytest tests/test_onboarding.py -v
```

---

## Интеграция с CI/CD

### GitHub Actions пример
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements-test.txt
      
      - name: Run tests
        run: |
          pytest tests/ -v --tb=short
```

---

## Контакты и поддержка

Для вопросов по тестам обращайтесь к документации:
- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
- [aiogram testing guide](https://docs.aiogram.dev/en/latest/dispatcher/testing.html)
