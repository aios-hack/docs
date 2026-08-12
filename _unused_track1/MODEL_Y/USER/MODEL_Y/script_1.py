#Automaticaly recalculate=true
#Single model=false
#Run for one model=false
# Automaticaly recalculate=true
# Single model=false
import datetime
import getpass
import math
import os
import pprint

import pandas as pd

print(type(get_all_models()))

#########################################################
N = 0  ### ВВЕДИТЕ ПОРЯДКОВЫЙ НОМЕР МОДЕЛИ  ИЗ СПИСКА (НАЧИНАЯ С 0)
#########################################################
keyword = {
    "grou": get_all_groups(),
    "wells": get_wells_from_filter("Фильтр по скважинам 1"),
    "mod": [get_all_models()[N]],
    "step": get_all_timesteps(),
}
user = getpass.getuser()
date = datetime.datetime.strftime(datetime.datetime.now(), "%d.%m.%y")


def create_report_dir(path):
    """Создает папку отчетов и делает ее текущей."""
    reports_path = r"E:\reports"
    if not os.path.exists(reports_path):
        os.makedirs(reports_path)
    os.chdir(reports_path)


def dataframe_creater(*args, start="01.01.2007", **kwarg):
    """Конвертирует навигационные данные в DataFrame."""
    indicators = [x for x in args]
    name = ["Parametr{}".format(x) for x in range(len(indicators))]
    indicators_dict = {x: [] for x in ["date", "well"] + name}
    assos_dict = dict(zip(indicators, name))
    start_date = datetime.datetime.strptime(start, "%d.%m.%Y")

    for m in kwarg["mod"]:
        for w in kwarg["wells"]:
            for t in kwarg["step"]:
                if t.to_datetime() >= start_date:
                    indicators_dict["date"].append(t.to_datetime())
                    indicators_dict["well"].append(w.name)
                    for i in indicators:
                        indicators_dict[assos_dict[i]].append(i[m, w, t].to_list()[0])
                else:
                    continue

    result = pd.DataFrame(indicators_dict, index=indicators_dict["date"])
    return result.drop("date", axis=1)


# Создаем папку для отчетов
create_report_dir(path=r"E:\reports")

# Создаем DataFrame из навигационных данных
df = pd.DataFrame(
    dataframe_creater(
        wlpt,
        wlpr,
        womt,
        womr,
        wwir,
        wwit,
        wbp9,
        wbhp,
        weff,
        start="01.01.2007",
        **keyword,
    )
)

# Вычисляем разности для определенных параметров
df["WLPT_Diff"] = df["Parametr0"].diff()
df["WOMT_Diff"] = df["Parametr2"].diff()
df["WWIT_Diff"] = df["Parametr5"].diff()
df = df.shift(periods=-1)

# === Переименование столбцов в нужной последовательности ===
df.reset_index(inplace=True)
df.columns = [
    "DATA",
    "well",
    "WLPT",
    "WLPR",
    "WOMT",
    "WOMR",
    "WWIR",
    "WWIT",
    "THP",
    "BHP",
    "WEFF",
    "WLPT_Diff",
    "WOMT_Diff",
    "WWIT_Diff",
]


# Сохранение в CSV
output_filename = f"Модель {get_all_models()[N].name}_{user}.csv"
df.to_csv(output_filename, index=False, encoding="utf-8-sig")

print(
    f"Модель {get_all_models()[N].name} экспортирована в таблицу (папка reports) под именем: {output_filename}"
)
