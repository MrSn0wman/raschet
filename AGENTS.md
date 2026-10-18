# Правила проекта «Расчёт.рф» (для агентов)

## Процесс

1. **После КАЖДОГО изменения — проверка в браузере субагентом.** Ни один коммит не уходит без живого прогона: headless Chrome (C:\Program Files\Google\Chrome\Application\chrome.exe), страница поднимается через `python -m http.server`, проверяются рендер, отсутствие JS-ошибок и затронутое поведение. Дизайн-изменения — ещё и скриншоты 320/1280, обе темы.
2. **Конвейер сборки** (`_build/build/`): `build_all.py` (генерация из `_build/parts/` + старых источников) → `fix_csp.py` → `integrate_pwa.py` (SW/манифест/аналитика) → `test_site.py` (79 страниц против baseline). SEO-пост-процессоры: `fix_seo_meta.py` (og:image/twitter/JSON-LD), `fix_titles.py` (title ≤60). Ручные правки страниц — только с зеркалированием в `_build/parts/` (style.css / header.html / footer.html / ui.js) и прогоном `sync_parts.py`, иначе пересборка откатит.
3. **Пуш:** `git push origin main` (креды в Windows Credential Manager). После пуша — проверить живой URL https://mrsn0wman.github.io/raschet/ после пересборки Pages (~1 мин).
4. **Дизайн** — субагент-критик по чек-листу `~/.dsh/design-critic.md` до PASS. **Код** — security-субагент по OWASP при изменениях логики/форм.
5. Числа с «₽» — с неразрывным пробелом (`\u00A0₽` в JS, `&nbsp;₽` в разметке). Случайность — только `crypto.getRandomValues` (см. `secureInt`/`secureIndex`). Пользовательский ввод — только через `textContent`/`esc()`, никакого innerHTML с ним.
