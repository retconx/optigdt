from enum import Enum
from PySide6.QtGui import QPalette, QColor

class farben(Enum):
    NORMAL = {}
    BLAU = {"dunkel" : (0, 0, 150), "hell" : (150, 200, 255)}
    GRUEN = {"dunkel" : (0, 150, 0), "hell" : (150, 255, 150)}
    ROT = {"dunkel" : (150, 0, 0), "hell" : (255, 150, 150)}
    GELB = {"dunkel" : (150, 0, 0), "hell" : (255, 150, 150)}
    TESTAUSAHL = {"dunkel" : (120, 120, 120), "hell" : (220, 220, 220)}
    CONCAT = {"dunkel" : (155, 120, 155), "hell" : (255, 220, 255)}
    ADDZEILE = {"dunkel" : (120, 155, 120), "hell" : (220, 255, 220)}
    CHANGEZEILE = {"dunkel" : (155, 120, 120), "hell" : (255, 220, 220)}
    CHANGETEST = {"dunkel" : (120, 120, 155), "hell" : (220, 220, 255)}
    TESTAUS6228 = {"dunkel" : (155, 155, 120), "hell" : (255, 255, 220)}
    BEFUNDAUSTEST = {"dunkel" : (120, 155, 155), "hell" : (220, 255, 255)}

@staticmethod
def getTextPalette(farbe:farben, aktuellePalette:QPalette):
    if farbe == farben.NORMAL:
        return aktuellePalette
    modus = "hell"
    if aktuellePalette.color(QPalette.Base).value() < 150: # type: ignore
        modus = "dunkel"
    r, g, b = farbe.value[modus]
    palette = QPalette()
    palette.setColor(QPalette.WindowText, QColor(r, g, b)) # type: ignore
    palette.setColor(QPalette.Base, QColor(r, g, b)) # type: ignore
    return palette

@staticmethod
def getTextColor(farbe:farben, aktuellePalette:QPalette):
    if farbe == farben.NORMAL:
        return aktuellePalette.color(QPalette.Base) # type: ignore
    modus = "hell"
    if aktuellePalette.color(QPalette.Base).value() < 150: # type: ignore
        modus = "dunkel"
    r, g, b = farbe.value[modus]
    return QColor(r, g, b)