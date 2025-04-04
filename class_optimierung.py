import xml.etree.ElementTree as ElementTree 
import class_gdtdatei, class_Enums

class OptimierungsfehlerException(Exception):
    def __init__(self, meldung):
        self.meldung = meldung
    def __str__(self):
        return "Optimierungsfehler: " + self.meldung
    
class Optimierung:
    def __init__(self, typ:str, bisherigesRoot:ElementTree.Element):
        self.typ = typ
        self.neueId = Optimierung.getNeueId(bisherigesRoot)

    @staticmethod
    def getNeueId(bisherigesRoot:ElementTree.Element):
        """
        Gibt eine neue eindeutige Id zurück
        Parameter:
            bisherigesRootelelemen:ElementTree.Element
        Return:
            Neue Id
        """
        optimierungElemente = bisherigesRoot.findall("optimierung")
        ids = []
        for optimierungElement in optimierungElemente:
            ids.append(int(str(optimierungElement.get("id"))))
        neueId = 0
        if len(ids) > 0:
            letzteId = ids[len(ids) - 1]
            neueId = letzteId + 1
            while neueId in ids: # eindeutig?
                neueId += 1
        return neueId
    
    @staticmethod
    def getTypVonId(templateRoot:ElementTree.Element, id:str):
        """
        Gibt den Optimierung-Typ einer Id zurück
        Parameter:
            templateRoot:ElementTree.Element
            id:str
        Return:
            Typ:str
        Exception GdtFehlerException, wenn Id nicht gefunden
        """
        typ = ""
        for optimierungElement in templateRoot.findall("optimierung"):
            pruefId = optimierungElement.get("id")
            if id == pruefId:
                typ = optimierungElement.get("typ")
                break
        if typ == "":
            raise class_gdtdatei.GdtFehlerException("id " + id + " in Template nicht gefunden")
        return typ
    
    @staticmethod
    def replaceOptimierungElement(bisherigesRoot:ElementTree.Element, id:str, neuesOptimierungElement:ElementTree.Element):
        """
        Ersetzt ein Optimierungs-Element im Template-Root
        Parameter:
            bisherigesRoot:ElementTree.Element
            id: zu ersetzende Optimierungs-Id
            neuesOptimierungElement:ElementTree.Element
        Return:
            Geändertes Template-Root:ElementTree.Element
        Exception:
            GdtFehlerException
        """
        neuesOptimierungElement.set("id", id)
        try:
            elementIndex = 0
            for optimierungElement in bisherigesRoot.findall("optimierung"):
                if optimierungElement.get("id") == id:
                    break    
                elementIndex += 1
            bisherigesRoot.remove(bisherigesRoot.findall("optimierung")[elementIndex])
            bisherigesRoot.insert(elementIndex, neuesOptimierungElement)
            return bisherigesRoot
        except:
            raise class_gdtdatei.GdtFehlerException("Fehler in der Funktion replaceOptimierungElement (Id: " + id + ")")
        
    @staticmethod
    def removeOptimierungElement(bisherigesRoot:ElementTree.Element, id:str):
        """
        Entfernt ein Optimierungs-Element im Template-Root
        Parameter:
            bisherigesRoot:ElementTree.Element
            id: zu ersetzende Optimierungs-Id
        Exception:
            GdtFehlerException
        """
        try:
            elementIndex = 0
            for optimierungElement in bisherigesRoot.findall("optimierung"):
                if optimierungElement.get("id") == id:
                    break    
                elementIndex += 1
            bisherigesRoot.remove(bisherigesRoot.findall("optimierung")[elementIndex])
            return bisherigesRoot
        except:
            raise class_gdtdatei.GdtFehlerException("Fehler in der Funktion removeOptimierungElement (Id: " + id + ")")

class OptiAddZeile(Optimierung):
    def __init__(self, feldkennung:str, inhalt:str, zeileEinfuegen:class_Enums.ZeileEinfuegen, bisherigesRoot:ElementTree.Element):
        super().__init__("addZeile", bisherigesRoot)
        self.feldkennung = feldkennung
        self.inhalt = inhalt
        self.zeileEinfuegen = zeileEinfuegen
        self.Id = self.neueId
    
    def getXml(self) -> ElementTree.Element:
        optimierungElement = ElementTree.Element("optimierung")
        optimierungElement.set("id", str(self.Id))
        optimierungElement.set("typ", self.typ)
        feldkennungElement = ElementTree.Element("feldkennung") 
        feldkennungElement.text = self.feldkennung
        inhaltElement = ElementTree.Element("inhalt")
        inhaltElement.text = self.inhalt
        optimierungElement.append(feldkennungElement)
        optimierungElement.append(inhaltElement)
        if self.zeileEinfuegen.feldkennung != "":
            zeileeinfuegenElement = ElementTree.Element("zeileeinfuegen")
            zeileeinfuegenElement.set("vornach", str(self.zeileEinfuegen.vorNach))
            vorkommenElement = ElementTree.Element("vorkommen")
            vorkommenElement.text = str(self.zeileEinfuegen.vorkommen)
            einfuegenFeldkennungElement = ElementTree.Element("feldkennung")
            einfuegenFeldkennungElement.text = self.zeileEinfuegen.feldkennung
            zeileeinfuegenElement.append(vorkommenElement)
            zeileeinfuegenElement.append(einfuegenFeldkennungElement)
            optimierungElement.append(zeileeinfuegenElement)
        return optimierungElement
    
class OptiChangeZeile(Optimierung):
    def __init__(self, feldkennung:str, neuerInhalt:str, alleZeilen:bool, bisherigesRoot:ElementTree.Element):
        super().__init__("changeZeile", bisherigesRoot)
        self.feldkennung = feldkennung
        self.neuerInhalt = neuerInhalt
        self.alleZeilen = alleZeilen
        self.Id = self.neueId

    def getXml(self) -> ElementTree.Element:
        optimierungElement = ElementTree.Element("optimierung")
        optimierungElement.set("id", str(self.Id))
        optimierungElement.set("typ", self.typ)
        az = "True"
        if not self.alleZeilen:
            az = "False"
        optimierungElement.set("alle", az)
        feldkennungElement = ElementTree.Element("feldkennung") 
        feldkennungElement.text = self.feldkennung
        neuerInhaltElement = ElementTree.Element("inhalt") 
        neuerInhaltElement.text = self.neuerInhalt
        optimierungElement.append(feldkennungElement)
        optimierungElement.append(neuerInhaltElement)
        return optimierungElement
    
class OptiDeleteZeile(Optimierung):
    def __init__(self, feldkennung:str, alleZeilen:bool, bisherigesRoot:ElementTree.Element):
        super().__init__("deleteZeile", bisherigesRoot)
        self.feldkennung = feldkennung
        self.alleZeilen = alleZeilen
        self.Id = self.neueId

    def getXml(self) -> ElementTree.Element:
        optimierungElement = ElementTree.Element("optimierung")
        optimierungElement.set("id", str(self.Id))
        optimierungElement.set("typ", self.typ)
        az = "True"
        if not self.alleZeilen:
            az = "False"
        optimierungElement.set("alle", az)
        feldkennungElement = ElementTree.Element("feldkennung") 
        feldkennungElement.text = self.feldkennung
        optimierungElement.append(feldkennungElement)
        return optimierungElement
    
class OptiDeleteTest(Optimierung):
    def __init__(self, eindeutigkeitskriterien:dict, bisherigesRoot:ElementTree.Element):
        super().__init__("deleteTest", bisherigesRoot)
        self.eindeutigkeitskriterien = eindeutigkeitskriterien.copy()
        self.Id = self.neueId
    
    def getXml(self) -> ElementTree.Element:
        optimierungElement = ElementTree.Element("optimierung")
        optimierungElement.set("id", str(self.Id))
        optimierungElement.set("typ", self.typ)
        eindeutigkeitskriterienElement = ElementTree.Element("eindeutigkeitskriterien")
        for eindeutigkeitskriterium in self.eindeutigkeitskriterien:
            feldkennung = str(eindeutigkeitskriterium)
            kriteriumElement = ElementTree.Element("kriterium")
            kriteriumElement.set("feldkennung", feldkennung)
            kriteriumElement.text = self.eindeutigkeitskriterien[eindeutigkeitskriterium]
            eindeutigkeitskriterienElement.append(kriteriumElement)
        optimierungElement.append(eindeutigkeitskriterienElement)
        return optimierungElement

class OptiChangeTest(Optimierung):
    def __init__(self, eindeutigkeitskriterien:dict, aenderungen:dict, bisherigesRoot:ElementTree.Element):
        super().__init__("changeTest", bisherigesRoot)
        self.eindeutigkeitskriterien = eindeutigkeitskriterien.copy()
        self.aenderungen = aenderungen.copy()
        self.Id = self.neueId
    
    def getXml(self) -> ElementTree.Element:
        optimierungElement = ElementTree.Element("optimierung")
        optimierungElement.set("id", str(self.Id))
        optimierungElement.set("typ", self.typ)
        eindeutigkeitskriterienElement = ElementTree.Element("eindeutigkeitskriterien")
        for eindeutigkeitskriterium in self.eindeutigkeitskriterien:
            feldkennung = str(eindeutigkeitskriterium)
            kriteriumElement = ElementTree.Element("kriterium")
            kriteriumElement.set("feldkennung", feldkennung)
            kriteriumElement.text = self.eindeutigkeitskriterien[eindeutigkeitskriterium]
            eindeutigkeitskriterienElement.append(kriteriumElement)
        optimierungElement.append(eindeutigkeitskriterienElement)
        for aenderung in self.aenderungen:
            feldkennung = str(aenderung)
            aenderungElement = ElementTree.Element("aenderung")
            aenderungElement.set("feldkennung", feldkennung)
            aenderungElement.text = self.aenderungen[aenderung]
            optimierungElement.append(aenderungElement)
        return optimierungElement
    
class OptiTestAus6228(Optimierung):
    def __init__(self, trennRegexPattern:str, erkennungstext:str, erkennungsspalte:int, ergebnisspalte:int, eindeutigkeitErzwingen:bool, ntesVorkommen:int, testIdent:str, testBezeichnung:str, testEinheit:str, bisherigesRoot:ElementTree.Element, angepassteErgebnisse:dict):
        super().__init__("testAus6228", bisherigesRoot)
        self.trenRegexPattern = trennRegexPattern
        self.erkennungstext = erkennungstext
        self.erkennungsspalte = erkennungsspalte
        self.ergebnisspalte = ergebnisspalte
        self.eindeutigkeitErzwingen = eindeutigkeitErzwingen
        self.ntesVorkommen = ntesVorkommen
        self.testIdent = testIdent
        self.testBezeichnung = testBezeichnung
        self.testEinheit = testEinheit
        self.angepassteErgebnisseDict = angepassteErgebnisse
        self.Id = self.neueId

    def getXml(self) -> ElementTree.Element:
        optimierungElement = ElementTree.Element("optimierung")
        optimierungElement.set("id", str(self.Id))
        optimierungElement.set("typ", self.typ)
        trennRegexPatternElement = ElementTree.Element("trennRegexPattern")
        trennRegexPatternElement.text = self.trenRegexPattern
        optimierungElement.append(trennRegexPatternElement)
        erkennungstextElement = ElementTree.Element("erkennungstext")
        erkennungstextElement.text = self.erkennungstext
        optimierungElement.append(erkennungstextElement)
        erkennungsspalteElement = ElementTree.Element("erkennungsspalte")
        erkennungsspalteElement.text = str(self.erkennungsspalte)
        optimierungElement.append(erkennungsspalteElement)
        ergebnisspalteElement = ElementTree.Element("ergebnisspalte")
        ergebnisspalteElement.text = str(self.ergebnisspalte)
        optimierungElement.append(ergebnisspalteElement)
        eindeutigkeiterzwingenElement = ElementTree.Element("eindeutigkeiterzwingen")
        eindeutigkeiterzwingenElement.text = str(self.eindeutigkeitErzwingen)
        optimierungElement.append(eindeutigkeiterzwingenElement)
        ntesVorkommenElement = ElementTree.Element("ntesvorkommen")
        ntesVorkommenElement.text = str(self.ntesVorkommen)
        optimierungElement.append(ntesVorkommenElement)
        testIdentElement = ElementTree.Element("testIdent")
        testIdentElement.text = self.testIdent
        optimierungElement.append(testIdentElement)
        testBezeichnungElement = ElementTree.Element("testBezeichnung")
        testBezeichnungElement.text = self.testBezeichnung
        optimierungElement.append(testBezeichnungElement)
        testEinheitElement = ElementTree.Element("testEinheit")
        testEinheitElement.text = self.testEinheit
        optimierungElement.append(testEinheitElement)
        if len(self.angepassteErgebnisseDict) > 0: # ab 2.12.0
            angepassteErgebnisseElement = ElementTree.Element("angepassteergebnisse")
            for ergebnis in self.angepassteErgebnisseDict:
                ergebnisElement = ElementTree.Element("ergebnis")
                originalElement = ElementTree.Element("original")
                angepasstElement = ElementTree. Element("angepasst")
                originalElement.text = ergebnis
                angepasstElement.text = self.angepassteErgebnisseDict[ergebnis]
                ergebnisElement.append(originalElement)
                ergebnisElement.append(angepasstElement)
                angepassteErgebnisseElement.append(ergebnisElement)
            optimierungElement.append(angepassteErgebnisseElement)
        return optimierungElement
    
class OptiBefundAusTest(Optimierung):
    def __init__(self, testuebernahmen:list, befundzeile:str, bisherigesRoot:ElementTree.Element):
        super().__init__("befundAusTest", bisherigesRoot)
        self.testuebernahmen = testuebernahmen
        self.befundzeile = befundzeile
        self.Id = self.neueId

    def getXml(self) -> ElementTree.Element:
        optimierungElement = ElementTree.Element("optimierung")
        optimierungElement.set("id", str(self.Id))
        optimierungElement.set("typ", self.typ)
        for testuebernahme in self.testuebernahmen:
            testElement = ElementTree.Element("test")
            eindeutigkeitskriterienElement = ElementTree.Element("eindeutigkeitskriterien")
            variableElement = ElementTree.Element("variable")
            for kriterium in testuebernahme.eindeutigkeitskriterien:
                kriteriumElement = ElementTree.Element("kriterium")
                kriteriumElement.set("feldkennung", kriterium)
                kriteriumElement.text = testuebernahme.eindeutigkeitskriterien[kriterium]
                eindeutigkeitskriterienElement.append(kriteriumElement)
            feldkennungElement = ElementTree.Element("feldkennung")
            nameElement = ElementTree.Element("name")
            feldkennungElement.text = testuebernahme.platzhalterFeldkennung
            nameElement.text = testuebernahme.platzhalterName
            variableElement.append(feldkennungElement)
            variableElement.append(nameElement)
            testElement.append(eindeutigkeitskriterienElement)
            testElement.append(variableElement)
            optimierungElement.append(testElement)
        befundElement = ElementTree.Element("befund")
        befundElement.text = self.befundzeile
        optimierungElement.append(befundElement)
        return optimierungElement

class OptiConcatInhalte(Optimierung):
    def __init__(self, feldkennung:str, einzufuegendesZeichen:class_Enums.EinzufuegendeZeichen, bisherigesRoot:ElementTree.Element):
        super().__init__("concatInhalte", bisherigesRoot)
        self.feldkennung = feldkennung
        self.einzufuegendesZeichen = einzufuegendesZeichen
        self.Id = self.neueId

    def getXml(self) -> ElementTree.Element:
        optimierungElement = ElementTree.Element("optimierung")
        optimierungElement.set("id", str(self.Id))
        optimierungElement.set("typ", self.typ)
        feldkennungElement = ElementTree.Element("feldkennung") 
        feldkennungElement.text = self.feldkennung
        optimierungElement.append(feldkennungElement)
        einzufuegendesZeichenElement = ElementTree.Element("einzufuegendeszeichen") 
        einzufuegendesZeichenElement.text = self.einzufuegendesZeichen.name
        optimierungElement.append(einzufuegendesZeichenElement)
        return optimierungElement

class OptiAddPdf(Optimierung):
    def __init__(self, originalpfad:str, originalname:str, speichername:str, dateiformat:str, bisherigesRoot:ElementTree.Element):
        super().__init__("addPdf", bisherigesRoot)
        self.originalpfad = originalpfad
        self.originalname = originalname
        self.speichername = speichername
        self.dateiformat = dateiformat
        self.Id = self.neueId

    def getXml(self) -> ElementTree.Element:
        optimierungElement = ElementTree.Element("optimierung")
        optimierungElement.set("id", str(self.Id))
        optimierungElement.set("typ", self.typ)
        originalpfadElement = ElementTree.Element("originalpfad")
        originalpfadElement.text = self.originalpfad
        optimierungElement.append(originalpfadElement)
        originalnameElement = ElementTree.Element("originalname")
        originalnameElement.text = self.originalname
        optimierungElement.append(originalnameElement)
        speichernameElement = ElementTree.Element("speichername")
        speichernameElement.text = self.speichername
        optimierungElement.append(speichernameElement)
        dateiformatElement = ElementTree.Element("dateiformat")
        dateiformatElement.text = self.dateiformat
        optimierungElement.append(dateiformatElement)
        return optimierungElement
