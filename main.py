#!/usr/bin/python3
import sys
import requests
import zipfile
import re
import json
import os
import logging
import datetime
import time
import json2html
from matplotlib import pyplot as pp
import numpy as np
import subprocess

dir_path = os.path.dirname(os.path.realpath(__file__))
URL_ACTUAL = "https://ssl.smn.gob.ar/dpd/zipopendata.php?dato=tiepre"
URL_FUTURE = "https://ssl.smn.gob.ar/dpd/zipopendata.php?dato=pron5d"
PATH_JSON_ACTUAL = "actual.json"
PATH_JSON_FUTURE = "future.json"
PATH_ZIP_ACTUAL  = "_act.zip"
PATH_ZIP_FUTURE  = "_ftr.zip"




def load_files():
    try:
        with open(PATH_JSON_ACTUAL,) as file:
            #TODO log
            actual_data = json.load(file)
    except IOError:
        # TODO log
        with open(PATH_JSON_ACTUAL,"wt") as file:
            actual_data = {"data": []}
            file.write(json.dumps(actual_data, indent=4))

    try:
        with open(PATH_JSON_FUTURE,) as file:
            #TODO log
            future_data = json.load(file)

        return actual_data,future_data
    except IOError:
        # TODO log
        return False
    



def download(url, save_path, chunk_size=128):
    r = requests.get(url, stream=True)
    with open(save_path, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            fd.write(chunk)




def parse_actual_zip(path):
    zip = zipfile.ZipFile(path)
    file = zip.read(zip.namelist()[0])
    file = file.decode("cp1252")

    try:
        data = re.search('Concordia;(.+?) /', file)
    except AttributeError:
        data = 'nope'
        # TODO log

    ret = {
            "date": "",
            "hour": "",
            "weather": "",
            "visibility": "",
            "temp": "",
            "unk": "",
            "humidity": "",
            "wind": "",
            "pressure": ""
          }

    ret["date"],ret["hour"],ret["weather"],ret["visibility"],ret["temp"],ret["unk"],ret["humidity"],ret["wind"],ret["pressure"] = data.group(1).split(";")
    ret["temp"] = float(ret["temp"])
    ret["humidity"] = float(ret["humidity"])
    ret["pressure"] = float(ret["pressure"])
    return ret




def main():
    logging.basicConfig(format='%(asctime)s [%(levelname)s]:%(message)s', filename='example.log', level=logging.DEBUG)
    logging.getLogger().setLevel(logging.INFO)
    logging.info("Descargando...")
    download(URL_ACTUAL, PATH_ZIP_ACTUAL)
    logging.info("Parsing...")
    now_dict = parse_actual_zip(PATH_ZIP_ACTUAL)
    actual_dict, future_dict = load_files()

    not_found = True
    for d in actual_dict["data"]:
        if d['date'] == now_dict["date"] and d['hour'] == now_dict["hour"]:
            logging.info("Datos ya existen de actualidad (%s %s), saltando...", now_dict["date"], now_dict["hour"])
            not_found = False
            break

    if not_found:
        actual_dict["data"].append(now_dict)
        logging.info("Datos nuevos obtenidos, agregando.")

    parsed_json = json.dumps(actual_dict, indent=4)

    with open(PATH_JSON_ACTUAL, 'wt') as f:
        f.write(parsed_json)
        logging.info("Datos actuales guardados.")

    html_table = json2html.json2html.convert(json = parsed_json)
    temps  = [d['temp'] for d in actual_dict["data"]]
    labels = [d['hour'] for d in actual_dict["data"]]
    x = np.arange(len(temps))
    pp.plot(x,temps)
    pp.xticks(x, labels)
    pp.savefig('graph.png')
    with open("index.html", 'wt') as f:
        f.write("<img src='graph.png'> \n")
        f.write(html_table)










if __name__ == '__main__':
    try:
        while True:
            print("Inicio ciclo de bucle")
            main()
            print("Durmiendo hasta", datetime.datetime.now() + datetime.timedelta(hours = 1))
            subprocess.call(["git", "add", "."])
            subprocess.call(["git", "commit", "-a", "-m", "'updated'"])
            subprocess.call(["git", "push"])
            time.sleep(3600)
    except KeyboardInterrupt:
        print('interrupted!')
