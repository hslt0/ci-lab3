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
