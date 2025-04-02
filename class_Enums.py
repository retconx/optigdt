from enum import Enum

class EinzufuegendeZeichen(Enum):
    Kein_Zeichen = ""
    Leerzeichen = " "
    Komma = ", "
    Strichpunkt = "; "

class ZeileEinfuegen:
    def __init__(self, vorNach:int, vorkommen:int, feldkennung:str):
        self.vorNach = vorNach # 0 = vor, 1 = nach
        self.vorkommen = vorkommen
        self.feldkennung = feldkennung