# Перенос Python в один пакет backend/

Вне очередей. Не назначено. Ветка `refactor`, в `main` не влита.

**Что измерено.** Целостность связки (λ, ЧДД, эмит, CLI) после переноса старых верхнеуровневых пакетов (`contracts/`, `bridge/`, `ui/`, `aios_cli/` и прочих, удалённых без обратной совместимости) в единый пакет `backend/`.

**Чем измерено.** Контрольные прогоны на чистом `python:3.12.7-slim-bookworm`: пересчёт λ из кеша, сверка ЧДД с эталоном, эмит, `selfcheck`/`npv`/`emit`.

**Число.** λ, пересчитанная из кеша, совпала с `aios/data/lambda-window-2007/lambda.json` (`max |Δλ| = 0.0`). ЧДД сходится с эталоном на `1.49e-08`. Эмит те же 1553298 байт и тот же `content_hash`.

**Вывод.** Перенос не сломал связку. Команды образа теперь `python -m backend.presentation.cli.*`, витрина — `python -m backend.presentation.ui_export.demo`. Слои и направление зависимостей стережёт `tests/architecture/test_layers.py`, корни путей — `backend.core.paths`. Добавлен слой запусков: `RunWorkflow` пишет `runs/<id>/` со статусами `searched` / `rejected` / `ready_to_submit`, CLI — `python -m backend.presentation.cli.run search|verify|full`.

**Что дальше.** Влить в `main`.
