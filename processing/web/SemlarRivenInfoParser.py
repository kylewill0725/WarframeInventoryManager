import json5 as json
import re
from dataclasses import dataclass
from enum import Enum

import numpy as np
import requests


class WeaponTypes(str, Enum):
    SHOTGUN = "Shotgun"
    RIFLE = "Rifle"
    PISTOL = "Pistol"
    MELEE = "Melee"


@dataclass
class Buff:
    short_name: str
    full_name: str
    rm_name: str
    sem_name: str
    prefix: str
    suffix: str
    unique_words: list
    base_value: np.float
    cursed_bonus: bool

    def __init__(self,
                 short_name="",
                 full_name="",
                 rm_name="",
                 sem_name="",
                 prefix="",
                 suffix="",
                 base_value=0,
                 cursed_bonus=False
                 ):
        self.short_name = short_name
        self.full_name = full_name
        self.rm_name = rm_name
        self.sem_name = sem_name
        self.prefix = prefix
        self.suffix = suffix
        self.base_value = base_value
        self.cursed_bonus = cursed_bonus



@dataclass
class Weapon:
    name: str
    sem_disposition: np.float
    type: WeaponTypes


@dataclass
class WeaponTypeData:
    Weapons: list
    Buffs: list

    def __init__(self, json, weapon_type):
        self.Weapons = []
        self.Buffs = []

        for w in json["Rivens"]:
            self.Weapons.append(Weapon(w["name"], w["disposition"], weapon_type))

        for b in json["Buffs"]:
            name = b["text"]
            name = re.sub(r"[\w]*?\|val\|[%s]?\s?", "", name)
            self.Buffs.append(Buff(sem_name=name, base_value=b["value"], cursed_bonus=("curse" in b)))


class SemlarData:
    Melee: WeaponTypeData
    Rifle: WeaponTypeData
    Pistol: WeaponTypeData
    Shotgun: WeaponTypeData

    def __init__(self, json):
        for wt in WeaponTypes:
            self.__setattr__(wt, WeaponTypeData(json[wt], wt))


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
    data = SemlarData(json_data)
    pass


if __name__ == "__main__":
    get_semlar_data()
