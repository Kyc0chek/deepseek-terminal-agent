# DeepSeek Terminal Agent

Терминальный ИИ-агент на базе DeepSeek с функционалом, аналогичным Claude Code и Codex. Агент работает в командной строке, может читать/редактировать файлы, выполнять команды shell, искать код и решать задачи программирования.

## Возможности

- 🤖 **DeepSeek API** — использует мощные модели DeepSeek (V3, R1) через OpenAI-совместимый API
- 📁 **Работа с файлами** — чтение, запись, редактирование файлов
- 🖥️ **Shell команды** — выполнение bash/shell команд в реальном времени
- 🔍 **Поиск** — поиск по файлам и содержимому
- 💭 **Режим Reasoning** — поддержка DeepSeek R1 с chain-of-thought
- 🧠 **Контекст** — умное управление контекстом и памятью
- 🔄 **REPL интерфейс** — интерактивный терминальный интерфейс

## Установка

```bash
# Клонировать репозиторий
git clone https://github.com/Kyc0chek/deepseek-terminal-agent.git
cd deepseek-terminal-agent

# Создать виртуальное окружение (рекомендуется)
python -m venv .venv

# Активировать окружение
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Настроить API ключ
cp .env.example .env
# Отредактировать .env — добавить DEEPSEEK_API_KEY
```

## Быстрый старт

```bash
# Запуск из корня проекта (рекомендуется):
python src/main.py

# Альтернативный способ:
python -m src.main
```

## Конфигурация

Создайте файл `.env` в корне проекта:

```env
DEEPSEEK_API_KEY=your-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
# или deepseek-reasoner для R1

# Опционально
MAX_TOKENS=8192
TEMPERATURE=0.7
WORKING_DIR=.
```

Получить API ключ: https://platform.deepseek.com/

## Использование

После запуска вы увидите приглашение `>`. Вводите задачи на естественном языке:

```
> Создай файл hello.py с функцией приветствия

> Найди все TODO комментарии в проекте

> Запусти тесты и исправь ошибки

> Объясни, как работает этот код
```

### Специальные команды

- `/exit` или `/quit` — выход
- `/clear` — очистить контекст
- `/model <name>` — сменить модель
- `/think` — включить режим reasoning (R1)
- `/tools` — показать доступные инструменты
- `/help` — справка

## Архитектура

```
src/
├── main.py          # Точка входа
├── agent.py         # Основной цикл агента
├── llm_client.py    # Клиент DeepSeek API
├── context.py       # Управление контекстом
├── repl.py          # REPL интерфейс
├── prompts.py       # System prompts
└── tools/
    ├── base.py      # Базовый класс инструмента
    ├── file_tools.py    # Работа с файлами
    ├── shell_tools.py   # Shell команды
    ├── search_tools.py  # Поиск
    └── registry.py      # Реестр инструментов
```

## Лицензия

MIT
