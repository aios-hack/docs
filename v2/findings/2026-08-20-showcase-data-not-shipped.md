# Данные витрины не входят ни в git, ни в образ

Вне очередей. Не назначено.

**Что измерено.** Воспроизводимость витрины (`web`) на чистом клоне и в Docker-образе.

**Чем измерено.** Разбор `frontend/.gitignore`, `.dockerignore`, `Dockerfile`, `docker/entrypoint.sh`, `aios_cli/`.

**Число.** `frontend/public/data/` исключён и `frontend/.gitignore`, и `.dockerignore`; генерации данных нет ни в `Dockerfile`, ни в `docker/entrypoint.sh`, ни в `aios_cli/`.

**Вывод.** На чистом клоне `docker build` + `web` отдаёт интерфейс без единого JSON — у организаторов витрина не воспроизведётся.

**Что дальше.** Не назначено. Владелец `frontend/` — Михаил.
