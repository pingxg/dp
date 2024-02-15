# -*- coding: utf-8 -*-

import os
import re
import pandas as pd
from dotenv import load_dotenv

import pdfplumber
from shareplum import Site
from shareplum import Office365
from shareplum.site import Version
from config.re_pattern_config import get_expressions
from services.sharepoint import download_file

load_dotenv()

TEMP_PATH = os.path.join(os.getcwd(), 'temp')

DEBUG = False


expressions = get_expressions()

# authcookie = Office365(
#     os.getenv('OFFICE_SITE'),
#     username=os.getenv('OFFICE_USN'),
#     password=os.getenv('OFFICE_PSW')
#     ).GetCookies()

# site = Site(
#     os.getenv('SHAREPOINT_SITE'),
#     version=Version.v365,
#     authcookie=authcookie
#     )  # go to the finance site

# folder = site.Folder(os.getenv('MASTER_DATA_DIR'))  # open the folder path
# master_data = folder.get_file(os.getenv('MASTER_DATA_FILENAME'))  # read master data from sharepoint


master_data = download_file(os.getenv('MASTER_DATA_PATH'))
master_location = pd.read_excel(master_data, sheet_name="Location")  # read "Location" tab


def info_extractor(text, vendor, location_master_data=master_location):
    """
    text: text extracted from pdf file.
    vendor: S-Business Oy or METOS OY AB, this option determines the vendor-specific regular expressions.
    location_master_data: dictionary with key as the name of sushibar, value is the Netsuite location external ID.
    output: dictionary with following structure
        {
        "location":"External ID",
        # "matched_result": "location name",
        "14_net": float,
        "24_net": float,
        "14": float,
        "24": float,
        "14_total": float,
        "24_total": float,
        "approver": "bw approver name"
        }
    """
    text = text.replace('\n', ' ').replace('\r', '').lower()
    text = text.replace('(', ' ').replace(')', ' ')
    text = text.replace('/', ' ')
    text = text.replace('espoon keskus', 'espoonkeskus')
    text = ' '.join(text.split())
    text = text.replace(" cid:228 ",
                        "ä").replace("sm-", "").replace("vakka-", "vakka")
    text = text.replace(str("Tuottajantie 41, 60100 SEINÄJOKI").lower(), "")
    text = text.replace(str("60100 SEINÄJOKI").lower(), "")
    text = text.replace(str("Kotipaikka: SEINÄJOKI").lower(), "")
    text = text.replace(str("helsingin mylly").lower(), "")

    if "firewok" in text.lower():
        is_firewok = True
    else:
        is_firewok = False

    if "sushibar" in text.lower():
        is_sushibar = True
    else:
        is_sushibar = False

    if DEBUG:
        print("Orignal text: ", text)
    output = {}

    location_identifier = dict(
        zip(master_location['bw_matching'], master_location['External ID']))
    location_identifier_copy = {}
    for k, v in location_identifier.items():
        if isinstance(k, str):

            splited_key = k.split(",")
            if len(splited_key) != 1:
                for i in splited_key:
                    location_identifier_copy[i.strip()] = v
            else:
                location_identifier_copy[k.strip()] = v

    text_list = set(re.sub(r"[^a-zA-Z öä-˜]", "", text).split(" "))
    lication_identifier_set = set(location_identifier_copy.keys())
    intersection_list = list(text_list.intersection(lication_identifier_set))
    if DEBUG:
        print("Intersection list: ", intersection_list)

    if len(intersection_list) >= 1:
        # if 'seinäjoki' in intersection_list:
        #     intersection_list.remove('seinäjoki')
        output['location'] = location_identifier_copy[intersection_list[-1]]
        if output['location'] == "L56" and is_firewok and not is_sushibar:
            output['location'] = "L67"
        if output['location'] == "L43" and is_firewok and not is_sushibar:
            output['location'] = "L72"
        if output['location'] == "L44":
            output['location'] = "L23"
    else:
        print("Location not matched!")

    loc_dict = dict(
        zip(master_location['External ID'], master_location['bw_approver']))
    loc_dict['L4'] = 'Seinäjoki, Sushibar'
    loc_dict['L5'] = 'Seppälä, Sushibar'
    loc_dict['L24'] = 'Lappeenranta, Sushibar'
    if expressions[vendor][2] == "manager":
        output['approver'] = loc_dict[output['location']]

    price_pattern = re.compile(expressions[vendor][1])

    matches = price_pattern.finditer(text)

    try:
        if vendor == "1381774":
            for i in matches:

                if i.group(1):
                    match = str(i.group(1).strip()).split(" ")
                    match_converted = [
                        float(i.replace(" ", "")) for i in match
                    ]

            if len(match_converted) == 4:
                if match_converted[0] == 14:
                    output["14"] = match_converted[1]
                    output["14_net"] = match_converted[2]
                    output["14_total"] = match_converted[3]
                elif match_converted[0] == 24:
                    output["24"] = match_converted[1]
                    output["24_net"] = match_converted[2]
                    output["24_total"] = match_converted[3]
            elif len(match_converted) == 8:
                if match_converted[0] == 14:
                    output["14"] = match_converted[1]
                    output["14_net"] = match_converted[2]
                    output["14_total"] = match_converted[3]
                    output["24"] = match_converted[5]
                    output["24_net"] = match_converted[6]
                    output["24_total"] = match_converted[7]
                elif match_converted[0] == 24:
                    output["14"] = match_converted[5]
                    output["14_net"] = match_converted[6]
                    output["14_total"] = match_converted[7]
                    output["24"] = match_converted[1]
                    output["24_net"] = match_converted[2]
                    output["24_total"] = match_converted[3]
        elif vendor == "1367729":
            for i in matches:
                if i.group(1):
                    if output['location'] == "L44":
                        output['location'] = "L310"

                    output["24_net"] = float(
                        str(i.group(1).strip()).replace(",",
                                                        ".").replace(" ", ""))
                    output["24"] = float(
                        str(i.group(2).strip()).replace(",",
                                                        ".").replace(" ", ""))
                    output["24_total"] = float(
                        str(i.group(3).strip()).replace(",",
                                                        ".").replace(" ", ""))
        elif vendor == "1578999":
            for i in matches:
                if i.group(1):
                    total_str = str(i.group(1).strip())
                    reduced_str = re.sub(r"[^-0-9., ]", '',total_str).split(" ")
                    value_list = []
                    for j in reduced_str:
                        if j != "":
                            value_list.append(float(
                                j.replace(",", "").strip()))

                    if len(value_list) == 3:
                        if value_list[0] == 14:
                            output["14"] = value_list[2]
                            output["14_net"] = value_list[1]
                            output["14_total"] = round(
                                value_list[2] + value_list[1], 2)
                        elif value_list[0] == 24:
                            output["24"] = value_list[2]
                            output["24_net"] = value_list[1]
                            output["24_total"] = round(
                                value_list[2] + value_list[1], 2)
                    elif len(value_list) == 6:
                        if value_list[0] == 14:
                            output["14"] = value_list[2]
                            output["14_net"] = value_list[1]
                            output["14_total"] = round(
                                value_list[2] + value_list[1], 2)
                            output["24"] = value_list[5]
                            output["24_net"] = value_list[4]
                            output["24_total"] = round(
                                value_list[5] + value_list[4], 2)
                        elif value_list[0] == 24:
                            output["14"] = value_list[5]
                            output["14_net"] = value_list[4]
                            output["14_total"] = round(
                                value_list[5] + value_list[4], 2)
                            output["24"] = value_list[2]
                            output["24_net"] = value_list[1]
                            output["24_total"] = round(
                                value_list[2] + value_list[1], 2)

        elif vendor == "1426362":
            for i in matches:
                if i.group(1):
                    total_str = str(
                        i.group(1).strip()).split(" alv 14% summa eur ")

                    reduced_list = [
                        float(
                            re.sub(r"[^-0-9., ]", '',
                                   j).replace(".", '').replace(",",
                                                               '.').strip())
                        for j in total_str
                    ]
                    output["14"] = reduced_list[1]
                    output["14_net"] = reduced_list[0]
                    output["14_total"] = round(
                        reduced_list[0] + reduced_list[1], 2)
        elif vendor == "1389643" or vendor == "1394052":
            for i in matches:
                if i.group(1):
                    total_str = str(i.group(1).strip()).split("14,00 %")
                    reduced_list = [
                        float(
                            re.sub(r"[^-0-9., ]", '',
                                   j).replace(".", '').replace(",",
                                                               '.').strip())
                        for j in total_str
                    ]
                    print(reduced_list)

                    output["14"] = reduced_list[1]
                    output["14_net"] = reduced_list[0]
                    output["14_total"] = round(
                        reduced_list[0] + reduced_list[1], 2)
        elif vendor == "1276917" or vendor == '1375629':
            for i in matches:
                total_str = str(i.group(1).strip()).replace(",",
                                                            ".").split(" ")

                new_list = []
                for item in total_str:
                    try:
                        new_list.append(float(item))
                    except ValueError:
                        pass  # skip items that cannot be converted to float

                if "14.00%" in total_str and "24.00%" in total_str and len(
                        new_list) == 4:
                    output["14"] = new_list[1]
                    output["14_net"] = new_list[0]
                    output["14_total"] = new_list[0] + new_list[1]
                    output["24"] = new_list[3]
                    output["24_net"] = new_list[2]
                    output["24_total"] = new_list[2] + new_list[3]
                elif "14.00%" in total_str and len(new_list) == 2:
                    output["14"] = new_list[1]
                    output["14_net"] = new_list[0]
                    output["14_total"] = new_list[0] + new_list[1]
                elif "24.00%" in total_str and len(new_list) == 2:
                    output["24"] = new_list[1]
                    output["24_net"] = new_list[0]
                    output["24_total"] = new_list[0] + new_list[1]
        elif vendor == "2000088":
            for i in matches:
                # total_str = str(i.group(1).strip()).replace(",",
                #                                             ".").split(" ")
                total_str = i.group(1).strip().replace(",", ".").replace(
                    " %", "%").split(" arvonlisävero ")
                for i in total_str:
                    if "0%" in i:
                        output["0"] = round(float(i.split(" ")[1]), 2)
                        output["0_net"] = output["0"]
                    if "14%" in i:
                        output["14"] = round(float(i.split(" ")[1]), 2)
                        output["14_net"] = round(output["14"] / 0.14, 2)
                        output["14_total"] = output["14"] + output["14_net"]
                    if "24%" in i:
                        output["24"] = round(float(i.split(" ")[1]), 2)
                        output["24_net"] = round(output["24"] / 0.24, 2)
                        output["24_total"] = output["24"] + output["24_net"]
        elif vendor == "1714901":
            for i in matches:
                total_str = i.group(1).strip().split(" ")
                total_str = [float(j) for j in total_str]
                if len(total_str) == 11:
                    output["14_net"] = total_str[1]
                    output["14"] = total_str[2]
                    output["14_total"] = total_str[3]
                    output["24_net"] = total_str[5]
                    output["24"] = total_str[6]
                    output["24_total"] = total_str[7]

        elif vendor == "2000009":
            for i in matches:
                total_str = [
                    *i.group(1).strip().replace(" ", "").replace(",", ".")
                ]
                for c in range(len(total_str)):
                    if total_str[c] == ".":
                        total_str.insert(c + 3, ' ')

                total_str_list = ''.join(total_str).strip().split(" ")
                total_str_list = [float(i) for i in total_str_list]

                if len(total_str_list) == 3 and total_str_list[
                        2] == total_str_list[1] + total_str_list[0]:
                    output["14_net"] = total_str_list[0]
                    output["14"] = total_str_list[1]
                    output["14_total"] = total_str_list[2]
        elif vendor == "1553180":
            for i in matches:
                total_str = i.group(1).strip().replace(" %", "%")
                total_str = total_str.replace(",", ".").split(" ")
                if "14%" in total_str and "24%" in total_str:
                    output["14_net"] = float(total_str[1])
                    output["14"] = float(total_str[2])
                    output["14_total"] = float(total_str[3])
                    output["24_net"] = float(total_str[5])
                    output["24"] = float(total_str[6])
                    output["24_total"] = float(total_str[7])
                elif "14%" in total_str:
                    output["14_net"] = float(total_str[1])
                    output["14"] = float(total_str[2])
                    output["14_total"] = float(total_str[3])
                elif "24%" in total_str:
                    output["24_net"] = float(total_str[1])
                    output["24"] = float(total_str[2])
                    output["24_total"] = float(total_str[3])

        elif vendor == "1433275":
            for i in matches:
                total_str = i.group(1).strip().replace(",", ".").split(" ")
                total_str = [float(i) for i in total_str]
                if len(total_str) == 4:
                    if total_str[1] == 14:
                        output["14_net"] = total_str[0]
                        output["14"] = total_str[2]
                        output["14_total"] = total_str[3]
                    elif total_str[1] == 24:
                        output["24_net"] = total_str[0]
                        output["24"] = total_str[2]
                        output["24_total"] = total_str[3]
                elif len(total_str) == 8:
                    pass
                    output["24_net"] = total_str[0]
                    output["24"] = total_str[2]
                    output["24_total"] = total_str[3]
                    output["14_net"] = total_str[4]
                    output["14"] = total_str[6]
                    output["14_total"] = total_str[7]

        elif vendor == "1301716":
            for i in matches:
                total_str = i.group(1).strip().replace(",", ".").split(" ")
                total_str = [float(i) for i in total_str]
        elif vendor == "1566645":
            for i in matches:
                total_str = i.group(1).strip().replace(",", ".").split(" ")
                total_str = [float(i) for i in total_str]
                output["24_net"] = total_str[1]
                output["24"] = total_str[2]
                output["24_total"] = total_str[3]
        elif vendor == "2000211" or vendor == "2000224":
            for i in matches:

                total_str = i.group(1).replace(",", ".").split("arvonlisävero")
                total_str = [
                    i.strip() for i in total_str if i != "" and i != " "
                ]
                for i in total_str:
                    if "0 % " in i:
                        output["0"] = float(i.replace("0 % ", ""))
                    if "14 % " in i:
                        output["14"] = float(i.replace("14 % ", ""))
                    if "24 % " in i:
                        output["24"] = float(i.replace("24 % ", ""))
                    if "a " in i:
                        output["net"] = float(
                            i.replace("a ", "").replace(" ", ""))
                if "net" in output and "24" not in output:
                    output["14_net"] = output["net"]
                    output["14_total"] = output["14_net"] + output["14"]
                if "net" in output and "14" not in output:
                    output["24_net"] = output["net"]
                    output["24_total"] = output["24_net"] + output["24"]
                if "net" in output and "14" in output and "24" in output:
                    output["24_net"] = output["24"] / 0.24
                    output["14_net"] = output["net"] - output["24"]
                    output["14_total"] = output["14_net"] + output["14"]
                    output["24_total"] = output["24_net"] + output["24"]

        elif vendor == "1357805" or vendor == "2000219":
            for i in matches:
                total_str = i.group(1).strip().replace(",", ".").split(" ")
                for j in range(len(total_str)):
                    if total_str[j] == "14%":
                        output["14_net"] = float(total_str[j + 1])
                        output["14"] = float(total_str[j + 3])
                        output["14_total"] = output["14_net"] + output["14"]
                    elif total_str[j] == "24%":
                        output["24_net"] = float(total_str[j + 1])
                        output["24"] = float(total_str[j + 3])
                        output["24_total"] = output["24_net"] + output["24"]

        myDict = {key: val for key, val in output.items() if val != 0}

    except:
        return "Check your input vendor information!"
    return myDict


if DEBUG:

    def read_pdf_text(path=TEMP_PATH, file_type='pdf'):
        files = [f for f in os.listdir(path) if os.path.isfile(f)]
        files = list(
            filter(
                lambda f: f.endswith(
                    (f'.{file_type}', f'.{file_type.upper()}')), files))
        if len(files) == 1:

            pdfToString = ""

            pdf = pdfplumber.open(files[0])
            for page in pdf.pages:

                pdfToString += page.extract_text()

            pdf.close()
            return pdfToString
