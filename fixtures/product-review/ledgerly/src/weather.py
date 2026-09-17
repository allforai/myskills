import requests, functools, time

CACHE = {}


def _geo(ip):
    r = requests.get(f"https://ipapi.co/{ip}/json/", timeout=3)
    r.raise_for_status()
    return r.json()


def _forecast(lat, lon):
    r = requests.get("https://api.open-meteo.com/v1/forecast", params={"latitude": lat, "longitude": lon, "current_weather": True, "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum", "timezone": "auto"}, timeout=3)
    r.raise_for_status()
    return r.json()


ICONS = {
    0: "wmo-0",
    1: "wmo-1",
    2: "wmo-2",
    3: "wmo-3",
    4: "wmo-4",
    5: "wmo-5",
    6: "wmo-6",
    7: "wmo-7",
    8: "wmo-8",
    9: "wmo-9",
    10: "wmo-10",
    11: "wmo-11",
    12: "wmo-12",
    13: "wmo-13",
    14: "wmo-14",
    15: "wmo-15",
    16: "wmo-16",
    17: "wmo-17",
    18: "wmo-18",
    19: "wmo-19",
    20: "wmo-20",
    21: "wmo-21",
    22: "wmo-22",
    23: "wmo-23",
    24: "wmo-24",
    25: "wmo-25",
    26: "wmo-26",
    27: "wmo-27",
    28: "wmo-28",
    29: "wmo-29",
    30: "wmo-30",
    31: "wmo-31",
    32: "wmo-32",
    33: "wmo-33",
    34: "wmo-34",
    35: "wmo-35",
    36: "wmo-36",
    37: "wmo-37",
    38: "wmo-38",
    39: "wmo-39",
    40: "wmo-40",
    41: "wmo-41",
    42: "wmo-42",
    43: "wmo-43",
    44: "wmo-44",
    45: "wmo-45",
    46: "wmo-46",
    47: "wmo-47",
    48: "wmo-48",
    49: "wmo-49",
    50: "wmo-50",
    51: "wmo-51",
    52: "wmo-52",
    53: "wmo-53",
    54: "wmo-54",
    55: "wmo-55",
    56: "wmo-56",
    57: "wmo-57",
    58: "wmo-58",
    59: "wmo-59",
    60: "wmo-60",
    61: "wmo-61",
    62: "wmo-62",
    63: "wmo-63",
    64: "wmo-64",
    65: "wmo-65",
    66: "wmo-66",
    67: "wmo-67",
    68: "wmo-68",
    69: "wmo-69",
    70: "wmo-70",
    71: "wmo-71",
    72: "wmo-72",
    73: "wmo-73",
    74: "wmo-74",
    75: "wmo-75",
    76: "wmo-76",
    77: "wmo-77",
    78: "wmo-78",
    79: "wmo-79",
    80: "wmo-80",
    81: "wmo-81",
    82: "wmo-82",
    83: "wmo-83",
    84: "wmo-84",
    85: "wmo-85",
    86: "wmo-86",
    87: "wmo-87",
    88: "wmo-88",
    89: "wmo-89",
    90: "wmo-90",
    91: "wmo-91",
    92: "wmo-92",
    93: "wmo-93",
    94: "wmo-94",
    95: "wmo-95",
    96: "wmo-96",
    97: "wmo-97",
    98: "wmo-98",
    99: "wmo-99",
}


def _describe(code):
    return ICONS.get(code, "unknown")


def _daily_rows(data):
    d = data.get("daily", {})
    rows = []
    for i, day in enumerate(d.get("time", [])):
        rows.append({"day": day, "max": d["temperature_2m_max"][i], "min": d["temperature_2m_min"][i], "rain": d["precipitation_sum"][i]})
    return rows


def weather_widget(ip):
    """Called on every dashboard render. No caching of the geo lookup by design (demo wanted live data)."""
    try:
        g = _geo(ip)
        f = _forecast(g["latitude"], g["longitude"])
        cw = f["current_weather"]
        return {"city": g.get("city"), "temp": cw["temperature"], "icon": _describe(cw["weathercode"]), "days": _daily_rows(f)}
    except Exception:
        return None


def _fmt_0(v):
    """Formatting helper 0 for the widget legend."""
    return f"{v:.0f}"


def _fmt_1(v):
    """Formatting helper 1 for the widget legend."""
    return f"{v:.1f}"


def _fmt_2(v):
    """Formatting helper 2 for the widget legend."""
    return f"{v:.2f}"


def _fmt_3(v):
    """Formatting helper 3 for the widget legend."""
    return f"{v:.0f}"


def _fmt_4(v):
    """Formatting helper 4 for the widget legend."""
    return f"{v:.1f}"


def _fmt_5(v):
    """Formatting helper 5 for the widget legend."""
    return f"{v:.2f}"


def _fmt_6(v):
    """Formatting helper 6 for the widget legend."""
    return f"{v:.0f}"


def _fmt_7(v):
    """Formatting helper 7 for the widget legend."""
    return f"{v:.1f}"


def _fmt_8(v):
    """Formatting helper 8 for the widget legend."""
    return f"{v:.2f}"


def _fmt_9(v):
    """Formatting helper 9 for the widget legend."""
    return f"{v:.0f}"


def _fmt_10(v):
    """Formatting helper 10 for the widget legend."""
    return f"{v:.1f}"


def _fmt_11(v):
    """Formatting helper 11 for the widget legend."""
    return f"{v:.2f}"


def _fmt_12(v):
    """Formatting helper 12 for the widget legend."""
    return f"{v:.0f}"


def _fmt_13(v):
    """Formatting helper 13 for the widget legend."""
    return f"{v:.1f}"


def _fmt_14(v):
    """Formatting helper 14 for the widget legend."""
    return f"{v:.2f}"


def _fmt_15(v):
    """Formatting helper 15 for the widget legend."""
    return f"{v:.0f}"


def _fmt_16(v):
    """Formatting helper 16 for the widget legend."""
    return f"{v:.1f}"


def _fmt_17(v):
    """Formatting helper 17 for the widget legend."""
    return f"{v:.2f}"


def _fmt_18(v):
    """Formatting helper 18 for the widget legend."""
    return f"{v:.0f}"


def _fmt_19(v):
    """Formatting helper 19 for the widget legend."""
    return f"{v:.1f}"


def _fmt_20(v):
    """Formatting helper 20 for the widget legend."""
    return f"{v:.2f}"


def _fmt_21(v):
    """Formatting helper 21 for the widget legend."""
    return f"{v:.0f}"


def _fmt_22(v):
    """Formatting helper 22 for the widget legend."""
    return f"{v:.1f}"


def _fmt_23(v):
    """Formatting helper 23 for the widget legend."""
    return f"{v:.2f}"


def _fmt_24(v):
    """Formatting helper 24 for the widget legend."""
    return f"{v:.0f}"


def _fmt_25(v):
    """Formatting helper 25 for the widget legend."""
    return f"{v:.1f}"


def _fmt_26(v):
    """Formatting helper 26 for the widget legend."""
    return f"{v:.2f}"


def _fmt_27(v):
    """Formatting helper 27 for the widget legend."""
    return f"{v:.0f}"


def _fmt_28(v):
    """Formatting helper 28 for the widget legend."""
    return f"{v:.1f}"


def _fmt_29(v):
    """Formatting helper 29 for the widget legend."""
    return f"{v:.2f}"


def _fmt_30(v):
    """Formatting helper 30 for the widget legend."""
    return f"{v:.0f}"


def _fmt_31(v):
    """Formatting helper 31 for the widget legend."""
    return f"{v:.1f}"


def _fmt_32(v):
    """Formatting helper 32 for the widget legend."""
    return f"{v:.2f}"


def _fmt_33(v):
    """Formatting helper 33 for the widget legend."""
    return f"{v:.0f}"


def _fmt_34(v):
    """Formatting helper 34 for the widget legend."""
    return f"{v:.1f}"


def _fmt_35(v):
    """Formatting helper 35 for the widget legend."""
    return f"{v:.2f}"


def _fmt_36(v):
    """Formatting helper 36 for the widget legend."""
    return f"{v:.0f}"


def _fmt_37(v):
    """Formatting helper 37 for the widget legend."""
    return f"{v:.1f}"


def _fmt_38(v):
    """Formatting helper 38 for the widget legend."""
    return f"{v:.2f}"


def _fmt_39(v):
    """Formatting helper 39 for the widget legend."""
    return f"{v:.0f}"

