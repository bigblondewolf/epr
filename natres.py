#!/usr/bin/env python3

"""Графика и статистика за Експат Природни Ресурси.

Викаме скрипта веднъж дневно, необходимо е логът да е в същата
директория.

Сваля документа с описанието на Експат Природни Ресурси и намира в него
текущата цена. Записва я в лога natres.log и изчертава графика на
движението на цената от началото на фонда.

Записва само нетната стойност на активите за един дял.

Няма начин автоматично да се изтегли информация за минал период, затова
ни трябва лога с досегашните данни. Периодично обновявам файла в репото.

Старите данни могат да се свалят от същата страница, в раздел
Документи -> Периодична информация като PDF. Прилично лесен начин за
сваляне на таблиците е с Okuklar и "Table Selection"
"""

import os

from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import requests as req

OUT_FN = "natres.html"
STORAGE = "natres.log"
ETF_URL = "https://www.expat.bg/bg/funds/ExpatNaturalResources"
headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5)'
                      ' AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/50.0.2661.102 Safari/537.36'}


def format_date(d):
    """Convert dd-mm-yyyy to yyyy-mm-dd."""
    dl = d.split(".")
    dl.reverse()
    return(".".join(dl))


def fetch_new():
    resp = req.get(ETF_URL, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    for (n, t) in enumerate(soup.find_all("table")):
        ths = t.find_all("th")
        if len(ths) == 1:
            if not ths[0].text.startswith("Обобщена информация към"):
                continue
        d = ths[0].text.split(" ")[-1]
        for tb in t.find_all("tbody"):
            for tr in tb.find_all("tr"):
                tds = tr.find_all("td")
                if tds[0].text == "Нетна стойност на активите за един дял":
                    ns = tds[1].text.split(" ")[1]
                    return((format_date(d), ns))


def store_data(d):
    """Записваме новите данни във файла"""

    if not os.path.exists(STORAGE):
        with open(STORAGE, "w") as file:
            file.write('"Дата" "Нетна стойност"\n')

    # Намира бързо последния ред в текста, за да не повторим ако вече
    # сме записвали днешните данни.
    # https://www.codingem.com/how-to-read-the-last-line-of-a-file-in-python/
    with open(STORAGE, "rb") as file:
        try:
            file.seek(-2, os.SEEK_END)
            while file.read(1) != b'\n':
                file.seek(-2, os.SEEK_CUR)
        except OSError:
            file.seek(0)
        last_line = file.readline().decode()
    if len(last_line) > 0:
        last_date = last_line.split(" ")[0]
        if d[0] == last_date:
            return()
    with open(STORAGE, "a") as file:
        file.write(" ".join(d) + "\n")


def read_log(lf):
    """Четем лога и връщаме pandas df."""
    return(pd.read_csv(lf, delimiter=" "))


def plot_nominal(df):
    """Рисуваме графиката."""
    fig = px.line(df, x="Дата", y="Нетна стойност",
                  title="Договорен фонд Експат Природни Ресурси",
                  template="simple_white")
    fig.write_html(OUT_FN)


def main():
    new_data = fetch_new()
    store_data(new_data)
    plot_nominal(read_log(STORAGE))


if __name__ == "__main__":
    main()
