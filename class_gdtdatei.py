from enum import Enum
import csv, os, re
import xml.etree.ElementTree as ElementTree
import class_Enums

gdtDefinitionsPfad = "qms/200105_GdtV21_definition.csv"
basedir = os.path.dirname(__file__)
reGdtDateiendungSequentiell = r"^\.\d{3}$"

class GdtFehlerException(Exception):
    def __init__(self, meldung):
        self.meldung = meldung
    def __str__(self):
        return "GDT-Fehler: " + self.meldung
    
class GdtZeichensatz(Enum):
    BIT_7 = 1
    IBM_CP437 = 2 # Standard
    ANSI_CP1252 = 3
    
class Test():
    def __init__(self, ident:str, eindeutigkeitsFeldkennungen:list=["8410"]):
        """
        Definiert einen Test
        Parameter:
            ident: Test-Ident (Feldkennung 8410)
            eindeutigkeitsFelkennungen: String-Liste von Feldkennungen, deren Inhalte beim Gleichheitsvergleich übereinstimmen müssen (standardmäßig 8410)
        """
        self.indent = ident
        self.eindeutigkeitsFeldkennungen = eindeutigkeitsFeldkennungen
        self.zulaessigeFeldkennungen = []
        for fk in GdtDatei.getTestFeldkennungen():
            self.zulaessigeFeldkennungen.append(fk[0])
        self.testzeilen = {}
        self.testzeilen["8410"] = ident
    
    def setZeile(self, feldkennung:str, inhalt:str):
        """
        Setzt den Inhalt einer Testzeile
        Parameter:
            feldkennung:str
            inhalt:str
        Exception:
            GdtFehlerException, wenn keine zulässige Test-Feldkennung
        """
        if feldkennung in self.zulaessigeFeldkennungen:
            self.testzeilen[feldkennung] = inhalt
        else:
            raise GdtFehlerException("Keine gültige Test-Feldkennung: " + feldkennung)
    
    def setEindeutigkeitsFeldkennungen(self, feldkennungen:list):
        self.eindeutigkeitsFeldkennungen.clear()
        for feldkennung in feldkennungen:
            self.eindeutigkeitsFeldkennungen.append(feldkennung)
    
    def getInhalt(self, feldkennung:str):
        """
        Gibt den Inhalt einer Testzeile zurück, sofern sie existiert
        Parameter: 
            feldkennung:str
        Exception:
            GdtFehlerException, falls Feldkennung nicht vorhanden
        """
        inhalt = ""
        try:
            inhalt = self.testzeilen[feldkennung]
        except:
            raise GdtFehlerException("Feldkennung " + feldkennung + " nicht vorhanden")
        return inhalt
    
    def getAnzahlTestzeilen(self):
        return len(self.testzeilen)
    
    def getTestzeilen(self):
        return self.testzeilen
        
    def __eq__(self, other):
        tempTest = other
        if re.match(r"^.+__\d{4}__$", tempTest.testzeilen["8410"]) != None: # Test aus 6228-Zeile
            tempTest.setZeile("8410", tempTest.testzeilen["8410"][0:-8])
        gleich = True
        for fk in self.eindeutigkeitsFeldkennungen:
            if fk in self.testzeilen and fk in tempTest.testzeilen:
                if self.testzeilen[fk] != tempTest.testzeilen[fk]:
                    gleich = False
                    break
            else:
                raise GdtFehlerException("Feldkennung " + fk + " nicht in beiden zu vergleichenden Tests definiert")
        return gleich
    
    def __str__(self):
        output = ""
        for zeile in self.testzeilen:
            output += zeile + ": " + self.testzeilen[zeile] + "\n"
        return output

class GdtDatei():
    def __init__(self, zeichensatz = GdtZeichensatz.IBM_CP437):
        self.zeichensatz = zeichensatz
        self.enc = "cp437"
        if zeichensatz == GdtZeichensatz.BIT_7:
            self.enc = "utf_7"
        elif zeichensatz == GdtZeichensatz.ANSI_CP1252:
            self.enc = "cp1252"
        self.zeilen = []
        self.dateipfad = ""

    def setSatzlaenge(self, anzahlZiffern:int=5):
        """
        Setzt die aktuelle Satzlänge der GDT-Datei (Feldkennung 8100)
        Parameter:
            anzahlZiffern:int
        """
        laenge = 9 + anzahlZiffern
        for zeile in self.zeilen:
            if zeile[3:7] != "8100":
                laenge += len(zeile[7:]) + 9
        laengeFormatiert = ("{:>05}".format(laenge))
        i = 0
        for i in range(len(self.zeilen)):
            if self.zeilen[i][3:7] == "8100":
                self.zeilen[i] = GdtDatei.getZeile("8100", laengeFormatiert)
    
    def laden(self, dateipfad:str):
        """Lädt eine GDT-Datei
        Parameter: 
            dateipfad
        Return:
            Liste der Dateizeilen ohne \r\n
        Exception:
            GdtFehlerException, wenn keine GDT-Datei (keine Feldkennung 8000) oder Ladefehler
        """
        self.dateipfad = dateipfad
        self.zeilen = []
        feldkennung8000Vorhanden = False
        try:
            with open(dateipfad, "r", encoding=self.enc) as gdtDatei:
                for zeile in gdtDatei:
                    if zeile[:7] == "0138000":
                        feldkennung8000Vorhanden = True
                    self.zeilen.append(zeile.strip())
            if not feldkennung8000Vorhanden:
                self.zeilen.clear()
                raise GdtFehlerException("Keine gültige GDT-Datei")
        except IOError as e:
            raise GdtFehlerException("IO-Fehler: " + str(e))
        except Exception as e:
            charmapMeldung = ""
            if "charmap" in str(e):
                charmapMeldung = "\nMöglicherweise wurde in den GDT-Einstellungen ein unpassender Zeichensatz ausgewählt."
            raise GdtFehlerException(str(e) + charmapMeldung)
        return self.zeilen
    
    def speichern(self, pfad:str, zeichensatz:GdtZeichensatz):
        """
        Speichert die GDT-Datei
            Return: True bei Erfolg, False bei Misserfolg
        """
        if zeichensatz == GdtZeichensatz.BIT_7:
            enc = "utf_7"
        elif zeichensatz == GdtZeichensatz.IBM_CP437:
            enc = "cp437"
        else:
            enc = "cp1252"

        try:
            with open(pfad, "w", encoding=enc, newline="") as fobj:
                for zeile in self.zeilen:
                    fobj.write(zeile + "\r\n")
            return True
        except:
            return False
    
    def setZeichensatz(self, zeichensatz:GdtZeichensatz):
        self.zeichensatz = zeichensatz
        self.enc = "cp437"
        if zeichensatz == GdtZeichensatz.BIT_7:
            self.enc = "utf_7"
        elif zeichensatz == GdtZeichensatz.ANSI_CP1252:
            self.enc = "cp1252"

    def getZeichensatz(self):
        return self.zeichensatz

    def getZeichensatzAlsPythonString(self):
        return self.enc
    
    def getZeilen(self):
        return self.zeilen
    
    def getZeilennummern(self, feldkennung:str):
        """
        Gibt die Zeilennummern des Vorkommens einer Feldkennung zurück
        Parameter:
            feldkennung:str
        Return:
            Liste mit Zeilennummern
        """
        zeilennummern = []
        zeile = 0
        while zeile < len(self.zeilen):
            fk = self.zeilen[zeile][3:7]
            if fk == feldkennung:
                zeilennummern.append(zeile)
            zeile += 1
        return zeilennummern
    
    def getTests(self):
        """
        Gibt eine Liste aller Tests
        Return:
            Test-Liste (Typ Test)
        """
        i = 0
        tests = []
        tempTest = Test("")
        innerhalbTest = False
        while i < len(self.zeilen):
            fk = self.zeilen[i][3:7]
            inhalt = self.zeilen[i][7:]
            if not innerhalbTest and fk == "8410":
                innerhalbTest = True
                tempTest = Test(inhalt, ["8410"])
            elif innerhalbTest and fk[0:2] == "84" and fk != "8410":
                tempTest.setZeile(fk, inhalt)
                if i == len(self.zeilen) - 1:
                    tests.append(tempTest)
            elif innerhalbTest and (fk[0:2] != "84" or fk == "8410"):
                innerhalbTest = False
                tests.append(tempTest)
                if fk == "8410":
                    i -= 1 # Damit dieser Test nicht übersprungen wird
            i += 1
        return tests
    
    def getTestAus6228Befund(self, trennRegexPattern:str, erkennungstext:str, erkennungsspalte:int, ergebnisspalte:int, eindeutigkeitErzwingen:bool, ntesVorkommen: int, testbezeichnung:str, testeinheit:str, testident:str, angepassteErgebnisse:dict):
        """
        Erzeugt einen Test aus einem 6228-Befundtext
        Parameter:
            trennRegexPattern:str Reglulärer Ausdruck, der die Trennung zwischen den Befundspalten definiert 
            erkennungstext:str 
            erkennungsspalte:int
            ergebnisspalte:int (8420 im erzeugten Test)
            eindeutigkeitErzwingen:bool
            ntesVorkommen:int
            testbezeichnung:str (8411 im erzeugten Test)
            testeinheit:str (8421 im erzeugten Test)
            testident:str (8410 im erzeugten Test)    
            angepassteErgebnisse:dict (k: Original-Ergebnis, v: angepasstes Ergebnis)
        Return:
            Test:Test  
        """
        alle6228s = self.get6228s(trennRegexPattern)
        neuerTest = Test(testident)
        erkennungstextGefunden = False
        gefundenN = 0
        for inhalt6228 in alle6228s:
            if erkennungsspalte < len(inhalt6228) and ergebnisspalte < len(inhalt6228) and erkennungstext in inhalt6228[erkennungsspalte]:
                erkennungstextGefunden = True
                gefundenN += 1
                if gefundenN == ntesVorkommen:
                    neuerTest.setZeile("8411", testbezeichnung)
                    testErgebnis = inhalt6228[ergebnisspalte]
                    if testErgebnis in angepassteErgebnisse:
                        testErgebnis = angepassteErgebnisse[testErgebnis]
                    neuerTest.setZeile("8420", testErgebnis)
                    neuerTest.setZeile("8421", testeinheit)
                    break
        if not erkennungstextGefunden:
            raise GdtFehlerException("6228-Erkennungstext " + erkennungstext + " zur Umwandlung in Test nicht gefunden")
        return neuerTest

    def get6228s(self, trennRegexPattern:str):
        """
        Gibt eine Liste aller 6228-Zeilen zurück, wobei die 6228-Zeilen als Liste gesplitter Abschnitte zurückgegeben werden
        Parameter:
            trennRegexPattern: Reglulärer Ausdruck, der die Trennung zwischen den Befundspalten definiert    
        Return:
            Liste einer String-Liste mit den Befundspalten
        """
        i = 0
        befundtexte = []
        while i < len(self.zeilen):
            fk = self.zeilen[i][3:7]
            inhalt = self.zeilen[i][7:]
            if fk == "6228":
                befundtexte.append(re.split(trennRegexPattern, inhalt))
            i += 1
        return befundtexte
    
    def getInhalte(self,feldkennung:str):
        """
        Gibt alle Inhalte einer Feldkennung zurück
        Parameter: 
            feldkennung:str
        Return:
            String-Liste aller Inhalte
        Exception:
            GdtFehlerException, falls Feldkennung nicht vorhanden
        """
        i = 0
        inhalte = []
        while i < len(self.zeilen):
            fk = self.zeilen[i][3:7]
            inhalt = self.zeilen[i][7:]
            if fk == feldkennung:
                inhalte.append(inhalt)
            i += 1
        # if len(inhalte) == 0:
        #     raise GdtFehlerException("Felkennung " + feldkennung + " nicht vorhanden")
        return inhalte
    
    def addZeile(self, feldkennung:str, inhalt:str, zeileEinfuegen:class_Enums.ZeileEinfuegen=class_Enums.ZeileEinfuegen(0, 1, "")):
        """
        Fügt der GDT-Datei eine Zeile hinzu
        Parameter:
            feldkennung:str
            inhalt:str
            zeileEinfuegen:dialogOptimierungAddZeile.ZeileEinfuegen
        """
        einfuegePosition = len(self.zeilen)
        position = 0
        vorkommen = 0
        if zeileEinfuegen.feldkennung != "":
            for zeile in self.zeilen:
                fk = zeile[3:7]
                if zeileEinfuegen.feldkennung == fk:
                    vorkommen += 1
                    if zeileEinfuegen.vorkommen == vorkommen:
                        if zeileEinfuegen.vorNach == 0:
                            einfuegePosition = position
                        else:
                            einfuegePosition = position + 1
                        break
                position += 1
        self.zeilen.insert(einfuegePosition, GdtDatei.getZeile(feldkennung, inhalt))
    
    def changeZeile(self, id:str, feldkennung:str, neuerInhalt:str, alleVorkommen:bool=False, vorschau:bool=False):
        """
        Ändert den Inhalt einer/aller GDT-Zeile(n) einer Feldkennung
        Parameter:
            id:str Optimierungs-Id
            feldkennung:str
            neuerInhalt:str
            alleVorkommen:bool 
            vorschau:bool Gelöschten Zeilen wird __id__ angehängt
        Exception:
            GdtFehlerException, wenn zu ändernde Zeile nicht gefunden
        """
        vorkommen = []
        i = 0
        while i < len(self.zeilen):
            fk = self.zeilen[i][3:7]
            if fk == feldkennung:
                vorkommen.append(i)
            i += 1
        if len(vorkommen) > 0:
            if not alleVorkommen:
                if vorschau:
                    self.zeilen[vorkommen[0]] = GdtDatei.getZeile(feldkennung, neuerInhalt) + "__" + id + "__"
                else:
                    self.zeilen[vorkommen[0]] = GdtDatei.getZeile(feldkennung, neuerInhalt)
            else:
                for i in range(len(vorkommen)):
                    if vorschau:
                        self.zeilen[i] = GdtDatei.getZeile(feldkennung, neuerInhalt) + "__" + id + "__"
                    else:
                        self.zeilen[i] = GdtDatei.getZeile(feldkennung, neuerInhalt)
        else:
            raise GdtFehlerException("Zu ändernde Zeile(n) mit der Feldkennung " + feldkennung + " nicht gefunden")
    
    def deleteZeile(self, id:str, feldkennung:str, alleVorkommen:bool=False, vorschau:bool=False):
        """
        Löscht eine/alle GDT-Zeile(n) einer Feldkennung
        Parameter:
            id:str Optimierungs-Id
            feldkennung:str
            alleVorkommen:bool 
            vorschau:bool Gelöschten Zeilen wird __id__ angehängt
        Exception:
            GdtFehlerException, wenn zu löschende Zeile nicht gefunden
        """
        vorkommen = []
        i = 0
        while i < len(self.zeilen):
            fk = self.zeilen[i][3:7]
            if fk == feldkennung:
                vorkommen.append(i)
            i +=1
        if len(vorkommen) > 0:
            if not alleVorkommen:
                if vorschau:
                    self.zeilen[vorkommen[0]] += "__" + id + "__"
                else:
                    self.zeilen.pop(vorkommen[0])
            else:
                j = len(vorkommen) - 1
                while j >= 0:
                    if vorschau:
                        self.zeilen[vorkommen[j]] += "__" + id + "__"
                    else:
                        self.zeilen.pop(vorkommen[j])
                    j -= 1
        else:
            raise GdtFehlerException("Zu löschende Zeile(n) mit der Feldkennung " + feldkennung + " nicht gefunden")

    def concatInhalte(self, id, feldkennung:str, einzufuegendesZeichen:class_Enums.EinzufuegendeZeichen, vorschau:bool=False):
        """
        Führt die Inhalte einer Feldkunnung in der Zeile des ersten Vorkommens der Feldkennung zusammen und fügt optional ein Zeichen zwischen den Inhalten ein
        Parameter:
            id:str Optimierungs-Id
            feldkennung:str
            einzufuegendesZeichen:EinzufuegendeZeichen
            vorschau:bool Zusammengefassten Zeilen wird __Optimierungs-Id__ angehängt
        """
        concat = ""
        zeilenMitFeldkennung = self.getZeilennummern(feldkennung)
        ersteZeileMitFeldkennung = zeilenMitFeldkennung[0]
        inhalte = self.getInhalte(feldkennung)
        i = 0
        for inhalt in inhalte:
            concat += inhalt
            if i < len(inhalte) - 1:
                concat += einzufuegendesZeichen.value
            i += 1
        if vorschau:
            self.zeilen[ersteZeileMitFeldkennung] = self.getZeile(feldkennung, concat + "__" + id + "__")
        else:
            self.zeilen[ersteZeileMitFeldkennung] = self.getZeile(feldkennung, concat)
        zeilenMitFeldkennung.pop(0)
        zeilenMitFeldkennung.reverse()
        for zeile in zeilenMitFeldkennung:
            self.zeilen.pop(zeile)

    def getErgebnisAusTest(self, test:Test):
        """
        Gibt Ergebnis und Einheit eines Tests zurück
        Parameter:
            test:Test
        Return:
            Ergebnis und Einheit als Tupel
        """
        ergebnis = ()
        alleTests = self.getTests()
        for pruefTest in alleTests:
            if test == pruefTest:
                ergebnis = (pruefTest.getInhalt("8420"), pruefTest.getInhalt("8421"))
        return ergebnis
    
    def getInhalteAusTest(self, test:Test, feldkennungen:list):
        """
        Gibt Inhalte eines Tests zurück
        Parameter:
            test:Test
            feldkennungen:list Liste der Feldkennungen der gewünschten Inhalte
        Return:
            Inhalte als Dictionary mit key: Feldkennung, value: Inhalt
        """
        ergebnis = {}
        alleTests = self.getTests()
        for pruefTest in alleTests:
            if test == pruefTest:
                for fk in feldkennungen:
                    ergebnis[fk] = pruefTest.getInhalt(fk)
        return ergebnis

    def changeTestinhalt(self, id, zuAendernderTest:Test, aenderungen:dict, vorschau:bool=False):
        """
        Ändert eine oder mehrere Testzeile(n)
        Parameter:
            id:str Optimierungs-Id
            zuAendernderTest: Zu ändernder Test (Typ Test). Der Test muss mindestens die Eindeutigkeitsfeldkennungen enthalten.
            anderungen: Dictionary der Änderungen mit key: Feldkennung und value: neuer Inhalt
            vorschau:bool Geänderten Tests wird __id__ angehängt
        Exception:
            GdtFehlerException, wenn keine Tests vorhanden oder zu ändernder Test nicht gefunden
        """
        if len(self.getZeilennummern("8410")) > 0:
            testidentZeilennummer = self.getZeilennummern("8410")[0] # Zeilennummer des ersten Testidents
            alleTests = self.getTests()
            gefundenerTest = Test("xxxx")
            for pruefTest in alleTests:
                if zuAendernderTest == pruefTest:
                    gefundenerTest = pruefTest
                    for aenderung in aenderungen:
                        zuAendernderTest.setZeile(aenderung, aenderungen[aenderung])
                    break
                else:
                    testidentZeilennummer += pruefTest.getAnzahlTestzeilen()
            zeile = testidentZeilennummer
            alleZeilenGefundenerTest = gefundenerTest.getTestzeilen()
            alleZeilenZuAendernderTest = zuAendernderTest.getTestzeilen()
            if gefundenerTest.getInhalt("8410") != "xxxx":
                while zeile < testidentZeilennummer + len(alleZeilenGefundenerTest):
                    feldkennung = self.zeilen[zeile][3:7]
                    if feldkennung in alleZeilenZuAendernderTest:
                        if self.zeilen[zeile][7:] != alleZeilenZuAendernderTest[feldkennung]:
                            if vorschau:
                                self.zeilen[zeile] = GdtDatei.getZeile(feldkennung, alleZeilenZuAendernderTest[feldkennung] + "__" + id + "__")
                            else:
                                self.zeilen[zeile] = GdtDatei.getZeile(feldkennung, alleZeilenZuAendernderTest[feldkennung])
                    zeile += 1
            else:
                raise GdtFehlerException("Zu ändernden Test mit der ID " + zuAendernderTest.getInhalt("8410") + " nicht gefunden")
        else:
                raise GdtFehlerException("Änderung des Tests mit der ID " + zuAendernderTest.getInhalt("8410") + " nicht möglich, da GDT-Datei keine gültigen Tests enthält (keine Feldkennung 8410)")
    
    def deleteTest(self, id, zuAendernderTest:Test, vorschau=False):
        """
        Löscht einen Test
        Parameter:
            id:str Optimierungs-Id
            zuAendernderTest: Zu ändernder Test (Typ Test). Der Test muss mindestens die Eindeutigkeitsfeldkennungen enthalten.
            vorschau:bool Gelöschten Tests wird __id__ angehängt
        Exception:
            GdtFehlerException, wenn keine Tests vorhanden oder zu löschender Test nicht gefunden
        """
        if len(self.getZeilennummern("8410")) > 0:
            testidentZeilennummer = self.getZeilennummern("8410")[0] # Zeilennummer des ersten Testidents
            alleTests = self.getTests()
            gefundenerTest = Test("xxxx")
            for pruefTest in alleTests:
                if zuAendernderTest == pruefTest:
                    gefundenerTest = pruefTest
                    break
                else:
                    testidentZeilennummer += pruefTest.getAnzahlTestzeilen()
            zeileBeginnTest = testidentZeilennummer
            zeileEndeTest = testidentZeilennummer + gefundenerTest.getAnzahlTestzeilen()  - 1
            if gefundenerTest.getInhalt("8410") != "xxxx":
                while zeileEndeTest >= zeileBeginnTest:
                    if vorschau:
                        self.zeilen[zeileEndeTest] += "__" + id + "__"
                    else:
                        self.zeilen.pop(zeileEndeTest)
                    zeileEndeTest -= 1
            else:
                raise GdtFehlerException("Zu löschenden Test mit der ID " + zuAendernderTest.getInhalt("8410") + " nicht gefunden")
        else:
            raise GdtFehlerException("Löschen des Tests mit der ID " + zuAendernderTest.getInhalt("8410") + " nicht möglich, da GDT-Datei keine gültigen Tests enthält (keine Feldkennung 8410)")

    def getBefundAusTest(self, test:Test, befund:str):
        """
        Erzeugt einen Befundtext aus einem Test
        Paramter:
            test:Test Test, aus dem die Test-Inhate übernommen werden sollen.
            befund:str Befundtext, in dem die Variablen ${TFKxxxx} durch den Test-Inhalt mit der Felkennung xxxx ersetzt werden
        Rückgabe:
            Die Testinhalte beinhaltender Befundtext
        """
        i = 0
        varPositionen = {}
        while i < len(befund):
            i = befund.find("${TFK", i)
            if i != -1:
                varPositionen[i] = befund[i + 5:i + 9] # key: Position, value = feldkennung
                i += 10
            else:
                break
        for position in varPositionen:
            feldkennung = varPositionen[position]
            ersetzt = test.getInhalt(feldkennung)
            befund = befund.replace("${TFK" + feldkennung + "}", ersetzt)
        return befund

    def replaceFkVariablen(self, zuErsetzen:str):
        """"
        Ersetzt """
        i = 0
        varPositionen = {}
        while i < len(zuErsetzen):
            i = zuErsetzen.find("${FK", i)
            if i != -1:
                varPositionen[i] = zuErsetzen[i + 4:i + 8] # key: Position, value = feldkennung
                i += 9
            else:
                break
        for position in varPositionen:
            feldkennung = varPositionen[position]
            ersetzt = self.getInhalte(feldkennung)[0]
            zuErsetzen = zuErsetzen.replace("${FK" + feldkennung + "}", ersetzt)
        return zuErsetzen
    
    def applyTemplateVonPfad(self,templatePfad:str):
        tree = ElementTree.parse(templatePfad)
        rootElement = tree.getroot()
        return self.applyTemplate(rootElement)
    
    def applyTemplate(self, rootElement:ElementTree.Element, vorschau=False):
        """
        Wendet ein OptiGDT-Template an
        Parameter:
            rootElement:ElemetTree.Element
            vorschau:bool True, wenn im optimierten TreeWidget gelöschte Zeilen durchgestrichen und hinzugefügte/editierte Zeilen farbig dargestellt werden sollen (__Optimierungs-Id__ angehängt)
        Return:
            String-Liste mit Fehlermeldungen
        Exception:
            GdtFehlerException, wenn Dateipfad unbekannt    
        """
        if self.dateipfad != "":
            self.laden(self.dateipfad)
            exceptions = []
            for optimierungElement in rootElement:
                typ = optimierungElement.get("typ")
                id = "{:>04}".format(optimierungElement.get("id"))
                if typ == "addZeile":
                    feldkennung = optimierungElement.find("feldkennung").text # type: ignore
                    inhalt = self.replaceFkVariablen(optimierungElement.find("inhalt").text) # type: ignore
                    zeileEinfuegen = class_Enums.ZeileEinfuegen(0, 1, "")
                    if optimierungElement.find("zeileeinfuegen") != None: #  ab 2.13.1
                            zeileEinfuegenElement = optimierungElement.find("zeileeinfuegen")
                            vorNach = int(str(zeileEinfuegenElement.get("vornach"))) # type:ignore
                            vorkommen = int(str(zeileEinfuegenElement.find("vorkommen").text)) # type:ignore
                            einfuegenFeldkennung = str(zeileEinfuegenElement.find("feldkennung").text) # type:ignore
                            zeileEinfuegen = class_Enums.ZeileEinfuegen(vorNach, vorkommen, einfuegenFeldkennung)
                    if feldkennung and inhalt:
                        if vorschau:
                            self.addZeile(feldkennung, inhalt + "__" + id + "__", zeileEinfuegen)
                        else:
                            self.addZeile(feldkennung, inhalt, zeileEinfuegen)
                    else:
                        exceptions.append("Zeile mit Feldkennung " + str(feldkennung) + " und Inhalt " + str(inhalt) + " nicht hinzugefügt (xml-Datei fehlerhaft)")
                elif typ == "changeZeile":
                    alle = optimierungElement.get("alle") == "True"
                    feldkennung = str(optimierungElement.find("feldkennung").text) # type: ignore
                    inhalt = self.replaceFkVariablen(str(optimierungElement.find("inhalt").text)) # type: ignore
                    if feldkennung:
                        try:
                            self.changeZeile(id, feldkennung, inhalt, alle, vorschau)
                        except GdtFehlerException as e:
                            exceptions.append(e.meldung)
                    else:
                        exceptions.append("Zeile(n) mit Feldkennung " + str(feldkennung) + " nicht geändert (xml-Datei fehlerhaft)")
                elif typ == "deleteZeile":
                    alle = optimierungElement.get("alle") == "True"
                    feldkennung = optimierungElement.find("feldkennung").text # type: ignore
                    if feldkennung:
                        try:
                            self.deleteZeile(id, feldkennung, alle, vorschau)
                        except GdtFehlerException as e:
                            exceptions.append(e.meldung)
                    else:
                        exceptions.append("Zeile(n) mit Feldkennung " + str(feldkennung) + " nicht gelöscht (xml-Datei fehlerhaft)")
                elif typ == "deleteTest":
                    eindeutigkeitskriterienElement = optimierungElement.find("eindeutigkeitskriterien")
                    eindeutigkeitskriterien = {}
                    for kriteriumElement in eindeutigkeitskriterienElement.findall("kriterium"): # type: ignore
                        eindeutigkeitskriterien[str(kriteriumElement.get("feldkennung"))] = str(kriteriumElement.text)
                    test = Test("xxxx", list(eindeutigkeitskriterien.keys()))
                    for kriterium in eindeutigkeitskriterien:
                        test.setZeile(kriterium, self.replaceFkVariablen(eindeutigkeitskriterien[kriterium]))
                    try:
                        self.deleteTest(id, test, vorschau)  
                    except GdtFehlerException as e:
                        exceptions.append(e.meldung)
                elif typ == "changeTest":
                    eindeutigkeitskriterienElement = optimierungElement.find("eindeutigkeitskriterien")
                    eindeutigkeitskriterien = {}
                    for kriteriumElement in eindeutigkeitskriterienElement.findall("kriterium"): # type: ignore
                        eindeutigkeitskriterien[str(kriteriumElement.get("feldkennung"))] = str(kriteriumElement.text)
                    test = Test("xxxx", list(eindeutigkeitskriterien.keys()))
                    for kriterium in eindeutigkeitskriterien:
                        test.setZeile(kriterium, self.replaceFkVariablen(eindeutigkeitskriterien[kriterium]))
                    aenderungen = {}
                    for aenderungElement in optimierungElement.findall("aenderung"):
                        feldkennung = str(aenderungElement.get("feldkennung"))
                        inhalt = str(aenderungElement.text)
                        aenderungen[feldkennung] = inhalt
                    try:
                        self.changeTestinhalt(id, test, aenderungen, vorschau)
                    except GdtFehlerException as e:
                        exceptions.append(e.meldung)
                elif typ == "testAus6228":
                    trennRegexPattern = str(optimierungElement.find("trennRegexPattern").text) # type: ignore
                    erkennungstext = str(optimierungElement.find("erkennungstext").text) # type: ignore
                    if erkennungstext == "None":
                        erkennungstext = ""
                    erkennungsspalte = int(str(optimierungElement.find("erkennungsspalte").text)) # type: ignore
                    ergebnisspalte = int(str(optimierungElement.find("ergebnisspalte").text)) # type: ignore
                    eindeutigkeitErzwingen = True
                    if optimierungElement.find("eindeutigkeiterzwingen") != None: # ab 2.10.1
                        eindeutigkeitErzwingen = optimierungElement.find("eindeutigkeiterzwingen").text == "True" # type:ignore
                    ntesVorkommen = 1
                    if optimierungElement.find("ntesvorkommen") != None: # ab 2.10.1
                        ntesVorkommen = int(optimierungElement.find("ntesvorkommen").text) # type:ignore
                    testident = str(optimierungElement.find("testIdent").text) # type: ignore
                    testbezeichnung = str(optimierungElement.find("testBezeichnung").text) # type: ignore
                    testeinheit = str(optimierungElement.find("testEinheit").text) # type: ignore
                    if testeinheit == "None":
                        testeinheit = ""
                    angepassteErgebnisseDict = {}
                    if optimierungElement.find("angepassteergebnisse"): # ab 2.12.0
                        angepassteErgebnisseElement = optimierungElement.find("angepassteergebnisse")
                        for ergebnisElement in angepassteErgebnisseElement.findall("ergebnis"): # type: ignore
                            original = ergebnisElement.find("original").text # type: ignore
                            angepasst = ergebnisElement.find("angepasst").text # type: ignore
                            angepassteErgebnisseDict[original] = angepasst
                    try:
                        neuerTest = self.getTestAus6228Befund(trennRegexPattern, erkennungstext, erkennungsspalte, ergebnisspalte, eindeutigkeitErzwingen, ntesVorkommen, testbezeichnung, testeinheit, testident, angepassteErgebnisseDict)
                        testZeilen = neuerTest.getTestzeilen()
                        for zeile in testZeilen:
                            if vorschau:
                                self.addZeile(zeile, testZeilen[zeile] + "__" + id + "__")
                            else:
                                self.addZeile(zeile, testZeilen[zeile])
                    except GdtFehlerException as e:
                        exceptions.append(e.meldung)
                elif typ == "befundAusTest":
                    variablenInhalt = {}
                    for testElement in optimierungElement.findall("test"):
                        eindeutigkeitskriterienElement = testElement.find("eindeutigkeitskriterien")
                        eindeutigkeitskriterien = {}
                        for kriteriumElement in eindeutigkeitskriterienElement.findall("kriterium"): # type: ignore
                            eindeutigkeitskriterien[str(kriteriumElement.get("feldkennung"))] = str(kriteriumElement.text)
                        test = Test("xxxx", list(eindeutigkeitskriterien.keys()))
                        for kriterium in eindeutigkeitskriterien:
                            try:
                                test.setZeile(kriterium, self.replaceFkVariablen(eindeutigkeitskriterien[kriterium]))
                            except GdtFehlerException as e:
                                exceptions.append(e.meldung)
                        variableElement = testElement.find("variable")
                        feldkennung = str(variableElement.find("feldkennung").text) # type: ignore
                        name = str(variableElement.find("name").text) # type: ignore
                        testGefunden = False
                        for pruefTest in self.getTests():
                            if test == pruefTest:
                                if re.match(r"^.+__\d{4}__$", pruefTest.getInhalt(feldkennung)) != None:
                                    variablenInhalt[name] = pruefTest.getInhalt(feldkennung)[0:-8]
                                else:
                                    variablenInhalt[name] = pruefTest.getInhalt(feldkennung)
                                testGefunden = True
                                break
                        if not testGefunden:
                            exceptions.append("Test mit der ID " + test.getInhalt("8410") + " zur Befunderstellung nicht gefunden")
                    befund = str(optimierungElement.find("befund").text) # type: ignore
                    for inhalt in variablenInhalt:
                        befund = befund.replace("${" + inhalt + "}", variablenInhalt[inhalt])
                    if vorschau:
                        # Auf gesetzte Zeilenumbrüche prüfen
                        for befundzeile in befund.split("//"):
                            self.addZeile("6220", befundzeile + "__" + id + "__")
                    else:
                        # Auf gesetzte Zeilenumbrüche wird in directoryChanged in main.py geüprüft
                        # Nicht ersetzte Variablen durch "-" ersetzen
                        befundBereinigt = re.sub(r"\$\{[^{}]+\}", "-", befund)
                        # Einheiten nach - entfernen
                        einheiten = self.getInhalte("8421")
                        for einheit in einheiten:
                            if ("-" + einheit) in befundBereinigt:
                                befundBereinigt = befundBereinigt.replace("-" + einheit, "-")
                            elif ("- " + einheit) in befundBereinigt:
                                befundBereinigt = befundBereinigt.replace("- " + einheit, "-")
                        self.addZeile("6220", befundBereinigt)
                elif typ == "concatInhalte":
                    feldkennung = str(optimierungElement.find("feldkennung").text) # type: ignore
                    einzufuegendesZeichen = class_Enums.EinzufuegendeZeichen.Kein_Zeichen
                    if optimierungElement.find("einzufuegendeszeichen") != None:
                        einzufuegendesZeichen = class_Enums.EinzufuegendeZeichen[str(optimierungElement.find("einzufuegendeszeichen").text)] # type: ignore
                    if feldkennung != "None" :
                        try:
                            self.concatInhalte(id, feldkennung, einzufuegendesZeichen, vorschau)
                        except GdtFehlerException as e:
                            exceptions.append(e.meldung)
                    else:
                        exceptions.append("Zusammenführen der Inhalte mit der Feldkennung " + feldkennung + " nicht möglich (xml-Datei fehlerhaft)")
                elif typ == "addPdf":
                    originalpfad = str(optimierungElement.find("originalpfad").text) # type: ignore
                    originalname = str(optimierungElement.find("originalname").text) # type: ignore
                    speichername = str(optimierungElement.find("speichername").text) # type: ignore
                    # Ab Version 2.5.0
                    dateiformat = "PDF"
                    if optimierungElement.find("dateiformat") != None:
                        dateiformat = str(optimierungElement.find("dateiformat").text) # type: ignore
                    if originalpfad != "None" and originalname != "None" and speichername != "None" :
                        if re.match(reGdtDateiendungSequentiell, self.dateipfad[-4:]) != None:
                            endung = self.dateipfad[-3:]
                            originalname = originalname.replace("${###}", endung)
                        untersuchungsdatum = ""
                        untersuchungszeit = ""
                        try:
                            untersuchungsdatum = self.getInhalte("6200")[0]
                        except:
                            pass
                        if untersuchungsdatum != "":
                            try:
                                untersuchungszeit = self.getInhalte("6201")[0]
                            except:
                                pass
                            originalname = originalname.replace("JJJJ", untersuchungsdatum[4:]).replace("MM", untersuchungsdatum[2:4]).replace("TT", untersuchungsdatum[:2])
                            if untersuchungszeit != "":
                                originalname = originalname.replace("HH", untersuchungszeit[:2]).replace("mm", untersuchungszeit[2:4]).replace("ss", untersuchungszeit[4:])
                            originalname = originalname.replace("${", "").replace("}", "")
                        if vorschau:
                            self.addZeile("6302", "optigdtAnhang" + "__" + id + "__")
                            self.addZeile("6303", dateiformat + "__" + id + "__")
                            self.addZeile("6304", speichername + "__" + id + "__")
                            self.addZeile("6305", os.path.join(originalpfad, originalname) + ".pdf" + "__" + id + "__")
                        else:
                            if os.path.exists(os.path.join(originalpfad, originalname) + ".pdf"):
                                self.addZeile("6302", "optigdtAnhang")
                                self.addZeile("6303", dateiformat)
                                self.addZeile("6304", speichername)
                                self.addZeile("6305", os.path.join(originalpfad, originalname) + ".pdf")
                            else:
                                exceptions.append("Anhang " + os.path.join(originalpfad, originalname) + ".pdf nicht angehängt, da nicht existiert")
                    else:
                        exceptions.append("PDF anhängen nicht möglich (xml-Datei fehlerhaft)")
            return exceptions
        else:
            raise GdtFehlerException("Templateanwendung nicht möglich, da GDT-Dateipfad unbekannt")
        
    # Statische Methoden
    @staticmethod
    def getDefinitionen():
        """
        Gibt alle Definitionen zurück
        Return:
            Liste von [Feldkennung, Bezeichnung, Länge, Typ]
        """
        csvzeilen = []
        with open(os.path.join(basedir, gdtDefinitionsPfad), newline="") as csvfile:
            reader = csv.reader(csvfile, delimiter=";")
            for row in reader:
                csvzeilen.append(row)
        return csvzeilen

    @staticmethod
    def getDefinition(fk:str):
        """
        Gibt die Definition einer Feldkennung zurück
        Parameter:
            fk: Feldkennung
        """
        for row in GdtDatei.getDefinitionen():
            testFk = row[0]
            if testFk == fk:
                return row[1]
        return "Felkennung" + fk + " nicht definiert"
        
    @staticmethod
    def getTestFeldkennungen():
        """
        Gibt alle Testfeldkennungen zurück
        Return:
            Liste von Tupeln (Feldkennung, Bezeichnung)
        """
        testFeldkennungen = []
        for fk in GdtDatei.getDefinitionen():
            if fk[0] != "8402" and fk[0][0:2] == "84":
                testFeldkennungen.append((fk[0], fk[1]))
        return testFeldkennungen

    @staticmethod
    def checkTest(test:Test, kriterien:dict):
            """
            Prüft einen Test auf Kriterien
            Parameter:
                test: zu überprüfender Test: Test
                krieterien: Dictionary mit Kriterien mit key: Feldkennung, value: Inhalt
            Return:
                True oder False
            """
            kriteriumeErfuellt = True
            for kriterium in kriterien:
                if test.testzeilen[kriterium] != kriterien[kriterium]:
                    kriteriumeErfuellt = False
                    break
            return kriteriumeErfuellt

    @staticmethod
    def getZeile(feldkennung:str, inhalt:str, mitZeilenumbruch:bool = False):
        """Gibt eine GDT-Zeile zurück
        Parameter:
            feldkennung:str
            inhalt:str
            mitZeilenumbruch:bool Fügt \r\n an, falls True
        """
        laenge = 9 + len(inhalt)
        zeilenumbruch = ""
        if mitZeilenumbruch:
            zeilenumbruch ="\r\n"
        return "{:>03}".format(str(laenge)) + feldkennung + inhalt + zeilenumbruch
    
    @staticmethod
    def getTemplateInfo(templatePfad:str):
        """
        Gibt die Template-Infos zurück
        Parametter:
            templatepfad:str
        Return:
            Tupel aus kennfeld, gdtIdGeraet, gdftDateiname, exportverzeichnis und immerGdtAlsExportDateiendung
        """
        tree = ElementTree.parse(templatePfad)
        root = tree.getroot()
        kennfeld = str(root.get("kennfeld"))
        gdtIdGeraet = str(root.get("gdtIdGeraet"))
        gdtDateiname = str(root.get("gdtDateiname"))
        exportverzeichnis = str(root.get("exportverzeichnis"))
        immerGdtAlsExportDateiendung = root.get("immergdtalsexportdateiendung") == "True"
        return kennfeld, gdtIdGeraet, gdtDateiname, exportverzeichnis, immerGdtAlsExportDateiendung