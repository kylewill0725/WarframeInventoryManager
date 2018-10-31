import json5 as json
import re
from dataclasses import dataclass
from enum import Enum

import numpy as np
import requests


class WeaponTypes(str, Enum):
    SHOTGUN = "shotgun"
    RIFLE = "rifle"
    PISTOL = "pistol"
    MELEE = "melee"


@dataclass
class Buff:
    short_name: str
    full_name: str
    rm_name: str
    sem_name: str
    prefix: str
    suffix: str
    unique_words: str
    base_value: np.float


@dataclass
class Weapon:
    name: str
    sem_disposition: np.float
    type: WeaponTypes

def get_semlar_data():
    #get html
    html = requests.get("https://semlar.com/rivencalc").text
    html_match = re.search(r"var RivenStuff = (.*?)\s+var RivenTypeOrder", html, flags=re.DOTALL)
    if html_match is None:
        print("Semlar parser failed to match regex.")
        return

    raw_json = html_match.groups()[0]
    raw_json_without_comments = re.sub(r"(?m)^\s*//.*\n?", "", raw_json)

    json_data = json.loads(raw_json_without_comments)
    pass


if __name__ == "__main__":
    get_semlar_data()
