#!/usr/bin/env python3
"""Перепроверка чисел по деку Model_Z.

Печатает все величины, на которые ссылаются context/04_models.md и
context/08_contracts.md. Правило CLAUDE.md: числа по деку перепроверять
парсингом, а не доверять записанному. Скрипт только читает.

Запуск:  python3 tools/check_deck_facts.py
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DECK = ROOT / "models" / "Model_Z" / "Model_Z.data"
SCH = ROOT / "models" / "Model_Z" / "Model_Z_sch.inc"

T0 = date(2007, 1, 1)
MONTHS = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}
# ключевые слова, у которых внутри блока перечисляются скважины
#
# COMPDAT, не COMPDATMD: организаторы пересобрали дек 15.08 под внешний
# симулятор — заканчивание задано индексами ячеек, а не измеренной глубиной
# вдоль траектории. WELLTRACK из дека исчез вместе с COMPDATMD.
WELL_KEYWORDS = ("WCONPROD", "WCONINJE", "COMPDAT", "WPIMULT")


def parse_date(line: str) -> date:
    day, month, year = line.strip().strip("/").split()
    return date(int(year), MONTHS[month], int(day))


def read_start() -> date:
    lines = DECK.read_text(encoding="utf-8", errors="replace").split("\n")
    for i, line in enumerate(lines):
        if line.strip() == "START":
            return parse_date(lines[i + 1])
    raise ValueError("в .DATA нет START")


def parse_schedule():
    """Разбор Model_Z_sch.inc.

    Возвращает список дат и список блоков (индекс даты, ключевое слово,
    строки блока). Индекс даты -1 означает блок до первой DATES.
    """
    lines = SCH.read_text(encoding="utf-8", errors="replace").split("\n")
    dates: list[date] = []
    blocks: list[tuple[int, str, list[str]]] = []
    i, di = 0, -1
    while i < len(lines):
        token = lines[i].strip()
        if token == "DATES":
            di += 1
            dates.append(parse_date(lines[i + 1]))
        elif token in WELL_KEYWORDS:
            j, rows = i + 1, []
            while j < len(lines) and lines[j].strip() != "/":
                row = lines[j].strip()
                if row.startswith("'"):
                    rows.append(row)
                j += 1
            blocks.append((di, token, rows))
            i = j
        i += 1
    return dates, blocks


def well_of(row: str) -> str:
    return row.split("'")[1]


def fields(row: str) -> list[str]:
    return [f for f in re.split(r"\s+", row.strip()) if f]


def main() -> None:
    start = read_start()
    dates, blocks = parse_schedule()
    t0_index = dates.index(T0)
    n_control = len(dates) - t0_index

    steps = {(b.year - a.year) * 12 + b.month - a.month for a, b in zip(dates, dates[1:])}
    lead_months = (dates[0].year - start.year) * 12 + dates[0].month - start.month

    print("=== 1. Временная ось")
    print(f"START дека                     {start}")
    print(f"DATES                          {len(dates)}: {dates[0]} … {dates[-1]}")
    print(f"шаг между соседними DATES, мес {sorted(steps)}")
    print(f"первый отчётный интервал       {lead_months} мес (START → первая DATES)")
    print(f"блоков до первой DATES         {sum(1 for di, _, _ in blocks if di < 0)}")
    print(f"индекс {T0} (с нуля)      {t0_index}")
    print(f"управляющих дат                {n_control}")
    print(f"замкнутых интервалов после t0  {n_control - 1} (после {dates[-1]} следующей DATES нет)")

    print("\n=== 2. Ключевые слова по шкале управления")
    counts: dict[str, list[int]] = defaultdict(list)
    for di, kw, _ in blocks:
        counts[kw].append(di)
    for kw in sorted(counts):
        after = [d for d in counts[kw] if d >= t0_index]
        print(f"{kw:10s} блоков {len(counts[kw]):4d}, из них после t0 {len(after)}")
    for di, kw, rows in blocks:
        if kw == "WPIMULT":
            print(f"           WPIMULT на {dates[di]} (индекс {di}), скважин {len(rows)}")

    print("\n=== 3. Ввод скважин в работу")
    first_seen: dict[str, int] = {}
    for di, kw, rows in blocks:
        if kw in ("WCONPROD", "WCONINJE"):
            for row in rows:
                first_seen.setdefault(well_of(row), di)
    before = sum(1 for d in first_seen.values() if d < t0_index)
    at_t0 = sorted(w for w, d in first_seen.items() if d == t0_index)
    later = sum(1 for d in first_seen.values() if d > t0_index)
    print(f"скважин в WCON* всего          {len(first_seen)}")
    print(f"впервые до t0                  {before}")
    print(f"впервые на шаге t0             {len(at_t0)} {at_t0}")
    print(f"впервые после t0               {later}")
    print(f"вводится внутри горизонта      {len(at_t0) + later}")

    print("\n=== 4. COMPDAT после t0: классификация записей")
    n_blocks = primary = modification = 0
    mixed = []
    for di, kw, rows in blocks:
        if kw != "COMPDAT" or di < t0_index:
            continue
        n_blocks += 1
        kinds = set()
        for row in rows:
            if first_seen.get(well_of(row), 10**6) >= di:
                primary += 1
                kinds.add("первичное заканчивание")
            else:
                modification += 1
                kinds.add("изменение действующей")
        if len(kinds) > 1:
            mixed.append(dates[di])
    print(f"блоков                         {n_blocks}")
    print(f"записей первичного заканчивания {primary}")
    print(f"записей по действующим         {modification}")
    print(f"блоков со смешанной семантикой {len(mixed)}: {mixed}")

    print("\n=== 5. SHUT")
    shut = defaultdict(int)
    for di, kw, rows in blocks:
        for row in rows:
            if kw in ("WCONPROD", "WCONINJE") and "'SHUT'" in row:
                shut[kw] += 1
                if di >= t0_index:
                    shut[kw + "_after_t0"] += 1
            elif kw == "COMPDAT" and " SHUT " in row:
                shut["COMPDAT"] += 1
    print(f"записей WCONPROD SHUT          {shut['WCONPROD']} (после t0 {shut['WCONPROD_after_t0']})")
    print(f"записей WCONINJE SHUT          {shut['WCONINJE']}")
    print(f"записей COMPDAT SHUT           {shut['COMPDAT']} (закрытие интервалов перфорации)")

    print("\n=== 6. Переводы под закачку")
    seen_prod, seen_inj, conversions = set(), set(), []
    for di, kw, rows in blocks:
        for row in rows:
            well = well_of(row)
            if kw == "WCONPROD":
                seen_prod.add(well)
            elif kw == "WCONINJE":
                if well in seen_prod and well not in seen_inj:
                    conversions.append((dates[di], well))
                seen_inj.add(well)
    after = [c for c in conversions if c[0] >= T0]
    print(f"переводов PROD → INJ всего     {len(conversions)}")
    print(f"из них после t0                {len(after)}")
    print(f"скважины                       {sorted(w for _, w in conversions)}")

    print("\n=== 7. Режимы фонда по датам")
    per_step: dict[int, dict[str, tuple[str, str, float]]] = defaultdict(dict)
    for di, kw, rows in blocks:
        if kw not in ("WCONPROD", "WCONINJE"):
            continue
        for row in rows:
            f = fields(row)
            well = f[0].strip("'")
            if kw == "WCONPROD":
                per_step[di][well] = ("PROD", f[1].strip("'"), float(f[6]))
            else:
                per_step[di][well] = ("INJ", f[2].strip("'"), float(f[4]))

    state: dict[str, tuple[str, str, float]] = {}
    snapshot: dict[date, tuple[int, int, float, float]] = {}
    for di, when in enumerate(dates):
        state.update(per_step.get(di, {}))
        prod = [v for v in state.values() if v[0] == "PROD" and v[1] == "OPEN"]
        inj = [v for v in state.values() if v[0] == "INJ" and v[1] == "OPEN"]
        snapshot[when] = (len(prod), len(inj), sum(v[2] for v in prod), sum(v[2] for v in inj))

    print("дата         доб.  нагн.  отбор  закачка  компенсация")
    watch = [date(y, 12, 1) for y in (1996, 2000, 2003, 2006)]
    watch += [T0] + [date(y, 12, 1) for y in (2012, 2018, 2024)] + [dates[-1]]
    for when in watch:
        p, i, q, qi = snapshot[when]
        print(f"{when}   {p:3d}   {i:3d}   {q:6.0f}   {qi:6.0f}   {qi / q:.2f}")

    print("\n=== 8. Смены режима в окне управления")
    changed = defaultdict(int)
    records = defaultdict(int)
    previous: dict[tuple[str, str], tuple[str, str, float]] = {}
    setpoints = defaultdict(list)
    for di in range(t0_index, len(dates)):
        for well, value in sorted(per_step.get(di, {}).items()):
            role = value[0]
            records[role] += 1
            setpoints[role].append(value[2])
            key = (well, role)
            if key in previous and previous[key] != value:
                changed[role] += 1
            previous[key] = value
    for role in ("PROD", "INJ"):
        share = changed[role] / records[role]
        print(f"{role:4s} записей {records[role]:6d}, смен режима {changed[role]:4d} = {share:.2%}")
    print("(не считаются: первое появление скважины и перевод из другой роли;")
    print(" смена статуса и смена уставки считаются вместе)")

    print("\n=== 9. Уровни уставок в окне управления")
    for role, unit in (("PROD", "LRAT"), ("INJ", "RATE")):
        values = sorted(setpoints[role])
        median = values[len(values) // 2]
        mean = sum(values) / len(values)
        low = sum(1 for v in values if v <= 20) / len(values)
        print(
            f"{role:4s} {unit}: медиана {median:.0f}, среднее {mean:.0f}, "
            f"диапазон {values[0]:.0f}…{values[-1]:.0f}, доля ≤ 20 м³/сут {low:.0%}, "
            f"уникальных значений {len(set(values))}"
        )

    print("\n=== 10. Объявление скважин")
    text = SCH.read_text(encoding="utf-8", errors="replace")
    head = text.index("\nDATES")
    nl = chr(10)
    print(f"WELSPECS блоков до первой DATES  {text[:head].count(nl + 'WELSPECS')}")
    print(f"WELSPECS блоков после            {text[head:].count(nl + 'WELSPECS')}")
    # считать только строки самого блока WELSPECS: до первой DATES есть ещё
    # RPTSCHED, чьи строки тоже начинаются с апострофа
    ws_start = text.index(nl + "WELSPECS") + 1
    ws_body = text[ws_start:head].split(nl)
    welspecs = set()
    for row in ws_body[1:]:
        if row.strip() == "/":
            break
        if row.strip().startswith("'"):
            welspecs.add(row.split("'")[1])
    print(f"скважин в начальном WELSPECS     {len(welspecs)}")
    in_wcon = {w for w in first_seen}
    print(f"WELSPECS == множество WCON*      {welspecs == in_wcon}")
    print(f"COMPDAT блоков до первой DATES   {text[:head].count(nl + 'COMPDAT')}")
    print("\n=== 11. Слова, снятые организаторами при пересборке под OPM (15.08)")
    for gone in ("WELLTRACK", "COMPDATMD", "WELTRAJ", "COMPTRAJ", "LGR", "CARFIN"):
        print(f"{gone:10s} вхождений {text.count(nl + gone)}")


if __name__ == "__main__":
    main()
