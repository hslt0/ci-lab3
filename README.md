# Лабораторна №3

Розміщення кораблів за правилами поля з рифами за допомогою генетичного алгоритму та алгоритму імітаційного відпалу.

## Запуск

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Відкрити у браузері: http://127.0.0.1:5000

За замовчуванням завантажується `variant04.json`.

## Структура проєкту

- `app.py` — створення Flask-застосунку та точка запуску.
- `routes.py` — веб-маршрути й API.
- `validation.py` — перевірка вхідного JSON-варіанта.
- `solver.py` — спільна логіка розміщення та алгоритми GA/SA.
- `templates/index.html` — розмітка сторінки.
- `static/css/styles.css` — стилі.
- `static/js/main.js` — робота з інтерфейсом і API.

## Формат координат

Рифи задаються як `[x, y]`, де `x` — номер стовпця зліва направо, а `y` —
номер рядка зверху вниз. Початок корабля в усіх API-відповідях і таблиці UI
також повертається як `(x, y)`.

## Експерименти

```powershell
python experiments.py
```

Скрипт запускає серії GA/SA та порівняння алгоритмів і записує
`ga_experiment.csv`, `sa_experiment.csv`, `ga_sa_comparison.csv`.
