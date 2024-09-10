def get_expressions():
    return expressions


expressions = {
    "1381774": [
        "S-Business Oy",
        r"alv % alv yht. alv 0 % yht. sis. alv ([-0-9. ​]+) yhteensä alv 0%",
        None,
    ],
    "1367729": [
        "METOS OY AB",
        r"veroton loppusumma ([-0-9., ​]+) arvonlisävero 25,50 % ([-0-9., ]+) yhteensä eur ([-0-9., ]+) metos oy ab",
        None,
    ],
    "1578999": [
        "Oy Golden Crop AB",
        r"tax base amount vat ([- 0-9vat.%, €​]+)",
        "manager",
    ],
    "1394052": [
        "HÄTÄLÄ OY F56451",
        r"veroton summa ([-0-9a-z.%, €​]+) lasku yhteensä",
        "manager",
    ],
    "1426362": [
        "Kalaneuvos Oy",
        r"_____________ ([-0-9a-z.%, €​]+) _____________",
        "manager",
    ],
    "1389643": [
        "FINNISH FRESHFISH OY",
        r"veroton summa ([-0-9a-z.%, €​]+) lasku yhteensä",
        "manager",
    ],
    "2000009": ["Fisu Pojat Oy", r"14% ([-0-9 ,]+)", "manager"],
    "1276917": [
        "KANTA-HÄMEEN TUORETUOTE OY",
        r"alv-erittely: netto: ([alvnetto:0-9, %-]+)",
        "manager",
    ],
    "1375629": [
        "Tukkutalo Heinonen Oy",
        r"alv-erittely: netto: ([alvnetto:0-9, %-]+)",
        "manager",
    ],
    "1714901": [
        "AGRICA AB",
        r"arvonlisäveroerittely: alv % netto vero brutto specifikation av mervärdesskatt: mvs % skatt ([0-9. -]+)",
        "manager",
    ],
    "1566645": [
        "Yellow Service Oy Grönroos",
        r"verokanta veroton vero yhteensä ([-0-9 ,]+)",
        "manager",
    ],
    "1433275": [
        "Kesko Oyj",
        r"alv erittely veron peruste alv % vero verollinen ([-0-9 ,]+)",
        "manager",
    ],
    "1553180": ["Oy Hartwall Ab", r"alv-erittely verokanta([-0-9 ,%]+)", "manager"],
    "2000224": [
        "FinBlu Safety Oy",
        r"yhteensäilman ([-0-9 ,%arvonlisävero]+)",
        "manager",
    ],
    "1357805": [
        "SPARTAO OY",
        r"veroprosentti veron peruste veron määrä([-0-9,. eur%]+)",
        "manager",
    ],
    "2000219": [
        "Firewok Finland Oy",
        r"veroprosentti veron peruste veron määrä([-0-9,. eur%]+)",
        "manager",
    ],
    "1301716": ["AB Tingstad Papper", r".*", "manager"],
}
