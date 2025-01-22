import re
import xml.etree.ElementTree as ElementTree
import  class_gdtdatei
from PySide6.QtGui import Qt, QFont, QAction
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QLineEdit,
    QMessageBox,
    QLabel,
    QComboBox,
    QPushButton,
    QListWidget
)

reFeldkennung = r"^\d{4}$"

class Testuebernahme:
    def __init__(self, platzhalterName:str, platzhalterFeldkennung:str, eindeutigkeitskriterien:dict):
        self.eindeutigkeitskriterien = eindeutigkeitskriterien # key: feldkennung, value: kriterium
        self.platzhalterName = platzhalterName
        self.platzhalterFeldkennung = platzhalterFeldkennung

class OptimierungBefundAusTest(QDialog):
    def __init__(self, gdtDateiOptimiert:class_gdtdatei.GdtDatei, maxeindeutigkeitskriterien:int, testuebernahmen:list, befundzeile:str, templateRoot:ElementTree.Element):
        super().__init__()
        self.gdtDateiOptimiert = gdtDateiOptimiert
        self.maxeindeutigkeitskriterien = maxeindeutigkeitskriterien
        self.testuebernahmen = testuebernahmen # Liste von Testuebernmahmen
        self.befundzeile = befundzeile

        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontNormal.setItalic(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)
        self.fontBoldItalic = QFont()
        self.fontBoldItalic.setBold(True)
        self.fontBoldItalic.setItalic(True)

        self.setWindowTitle("GDT-Optimierung: Befundzeile aus Test(s)")
        self.setMinimumWidth(500)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type:ignore
        self.buttonBox.rejected.connect(self.reject) # type:ignore

        dialogLayoutVMain = QVBoxLayout()
        dialogLayoutHMain = QHBoxLayout()
        dialogLayoutVTestuebernahmeDefinieren = QVBoxLayout()
        dialogLayoutVTestuebernahmen = QVBoxLayout()
        dialogLayoutG = QGridLayout()
        groupBoxTestuebernahmeDefinieren = QGroupBox("Testübernahme definieren")
        groupBoxTestuebernahmeDefinieren.setFont(self.fontBold)
        groupBoxTestuebernahmeDefinieren.setLayout(dialogLayoutVTestuebernahmeDefinieren)

        groupBoxEindeutigkeitskriterien = QGroupBox("Eindeutigkeitskriterien")
        groupBoxEindeutigkeitskriterien.setFont(self.fontBoldItalic)
        groupBoxEindeutigkeitskriterien.setLayout(dialogLayoutG)
        labelFeldkennungen = []
        labelKriterien = []
        self.lineEditFeldkennungen = []
        self.lineEditKriterien = []
        self.pushButtonText = []
        self.pushButtonVariable = []
        for i in range(self.maxeindeutigkeitskriterien):
            labelFeldkennungen.append(QLabel("Feldkennung"))
            labelFeldkennungen[i].setFont(self.fontNormal)
            labelKriterien.append(QLabel("Kriterium"))
            labelKriterien[i].setFont(self.fontNormal)
            self.lineEditFeldkennungen.append(QLineEdit())
            self.lineEditFeldkennungen[i].setFont(self.fontNormal)
            self.lineEditKriterien.append(QLineEdit())
            self.lineEditKriterien[i].setFont(self.fontNormal)
            self.pushButtonText.append(QPushButton("T"))
            self.pushButtonText[i].setFont(self.fontNormal)
            self.pushButtonText[i].setToolTip("Text einfügen")
            self.pushButtonText[i].clicked.connect(lambda checked = False, lineEditFeldkennung = self.lineEditFeldkennungen[i], lineEditKriterium = self.lineEditKriterien[i]: self.pushButtonTextClicked(checked, lineEditFeldkennung, lineEditKriterium)) # type: ignore
            self.pushButtonVariable.append(QPushButton("V"))
            self.pushButtonVariable[i].setFont(self.fontNormal)
            self.pushButtonVariable[i].setToolTip("Variable einfügen")
            self.pushButtonVariable[i].clicked.connect(lambda checked = False, lineEditFeldkennung = self.lineEditFeldkennungen[i], lineEditKriterium = self.lineEditKriterien[i]: self.pushButtonVariableClicked(checked, lineEditFeldkennung, lineEditKriterium)) # type: ignore
            dialogLayoutG.addWidget(labelFeldkennungen[i], i * 2, 0, 1, 1)
            dialogLayoutG.addWidget(labelKriterien[i], i * 2, 1, 1, 1)
            dialogLayoutG.addWidget(self.lineEditFeldkennungen[i], i * 2 + 1, 0, 1, 1)
            dialogLayoutG.addWidget(self.lineEditKriterien[i], i * 2 + 1, 1, 1, 1)
            dialogLayoutG.addWidget(self.pushButtonText[i], i * 2 + 1, 2, 1, 1)
            dialogLayoutG.addWidget(self.pushButtonVariable[i], i * 2 + 1, 3, 1, 1)
        
        dialogLayoutHTextVariable = QHBoxLayout()
        groupBoxTextVariableEinfuegen = QGroupBox("Als Text (T) oder Variable (V) einfügen")
        groupBoxTextVariableEinfuegen.setFont(self.fontBoldItalic)
        groupBoxTextVariableEinfuegen.setLayout(dialogLayoutHTextVariable)
        labelTextVariable = QLabel("Verfügbare Feldkennungen/Inhalte")
        labelTextVariable.setFont(self.fontNormal)
        self.comboBoxTextVariable = QComboBox()
        self.comboBoxTextVariable.setFont(self.fontNormal)
        self.comboBoxTextVariable.setEditable(False)
        self.comboBoxTextVariable.setFixedWidth(300)
        self.comboBoxTextVariable.width
        i = 0
        for zeile in gdtDateiOptimiert.getZeilen():
            if re.match(r"^.+__\d{4}__$", zeile):
                self.comboBoxTextVariable.addItem(zeile[3:7] + ": " + zeile[7:-8])
            else:
                self.comboBoxTextVariable.addItem(zeile[3:7] + ": " + zeile[7:])
            i += 1
        dialogLayoutHTextVariable.addWidget(labelTextVariable)
        dialogLayoutHTextVariable.addWidget(self.comboBoxTextVariable)
        dialogLayoutG.addWidget(groupBoxTextVariableEinfuegen, (self.maxeindeutigkeitskriterien - 1) * 2 + 2, 0, 1, 4)

        dialogLayoutGPlatzhalter = QGridLayout()
        groupBoxPlatzhalter = QGroupBox("Platzhalter")
        groupBoxPlatzhalter.setFont(self.fontBold)
        groupBoxPlatzhalter.setLayout(dialogLayoutGPlatzhalter)
        labelPlatzhalterFeldkennung = QLabel("Feldkennung")
        labelPlatzhalterFeldkennung.setFont(self.fontNormal)
        labelPlatzhalterName = QLabel("Bezeichnung")
        labelPlatzhalterName.setFont(self.fontNormal)
        self.lineEditPlatzhalterFeldkennung = QLineEdit()
        self.lineEditPlatzhalterFeldkennung.setFont(self.fontNormal)
        self.lineEditPlatzhalterName = QLineEdit()
        self.lineEditPlatzhalterName.setFont(self.fontNormal)
        dialogLayoutGPlatzhalter.addWidget(labelPlatzhalterFeldkennung, 0, 0)
        dialogLayoutGPlatzhalter.addWidget(labelPlatzhalterName, 0, 1)
        dialogLayoutGPlatzhalter.addWidget(self.lineEditPlatzhalterFeldkennung, 1, 0)
        dialogLayoutGPlatzhalter.addWidget(self.lineEditPlatzhalterName, 1, 1)
        pushButtonTestuebernahmeHinzufuegen = QPushButton("Den Testübernahmen hinzufügen")
        pushButtonTestuebernahmeHinzufuegen.setFont(self.fontNormal)
        pushButtonTestuebernahmeHinzufuegen.clicked.connect(self.pushButtonTestuebernahmeHinzufuegenClicked) # type: ignore

        dialogLayoutVTestuebernahmeDefinieren.addWidget(groupBoxEindeutigkeitskriterien)
        dialogLayoutVTestuebernahmeDefinieren.addWidget(groupBoxPlatzhalter)
        dialogLayoutVTestuebernahmeDefinieren.addWidget(pushButtonTestuebernahmeHinzufuegen)

        groupBoxTestuebernahmen = QGroupBox("Testübernahmen")
        groupBoxTestuebernahmen.setFont(self.fontBold)
        groupBoxTestuebernahmen.setLayout(dialogLayoutVTestuebernahmen)
        self.listWidgetTestuebernahmen = QListWidget()
        self.listWidgetTestuebernahmen.setFont(self.fontNormal)
        self.listWidgetTestuebernahmen.currentItemChanged.connect(self.listWidgetTestuebernahmeItemChanged) # type: ignore
        self.listWidgetTestuebernahmen.itemDoubleClicked.connect(self.pushButtonUebernahmeEinfuegenClicked) # type: ignore
        dialogLayoutVTestuebernahmen.addWidget(self.listWidgetTestuebernahmen)

        # Contextmenü
        self.listWidgetTestuebernahmen.setContextMenuPolicy(Qt.ActionsContextMenu) # type:ignore
        self.testuebernahmeEntfernenAction = QAction("Testübernahme entfernen", self)
        self.testuebernahmeEntfernenAction.triggered.connect(self.testuebernahmeEntfernen) # type:ignore
        self.listWidgetTestuebernahmen.addAction(self.testuebernahmeEntfernenAction)

        dialogLayoutVBefundzeile = QVBoxLayout()
        groupBoxBefundzeile = QGroupBox("Befundzeile (Zeilenumbruch mit \"//\")")
        groupBoxBefundzeile.setFont(self.fontBold)
        groupBoxBefundzeile.setLayout(dialogLayoutVBefundzeile)
        self.lineEditBefundzeile = QLineEdit(self.befundzeile)
        self.lineEditBefundzeile.setFont(self.fontNormal)
        self.pushButtonUebernahmeEinfuegen = QPushButton("Testübernahme einfügen")
        self.pushButtonUebernahmeEinfuegen.setFont(self.fontNormal)
        self.pushButtonUebernahmeEinfuegen.clicked.connect(self.pushButtonUebernahmeEinfuegenClicked) # type:ignore
        dialogLayoutVBefundzeile.addWidget(self.lineEditBefundzeile)
        dialogLayoutVBefundzeile.addWidget(self.pushButtonUebernahmeEinfuegen)

        dialogLayoutHMain.addWidget(groupBoxTestuebernahmeDefinieren)
        dialogLayoutHMain.addWidget(groupBoxTestuebernahmen)
        dialogLayoutVMain.addLayout(dialogLayoutHMain)
        dialogLayoutVMain.addWidget(groupBoxBefundzeile)
        dialogLayoutVMain.addWidget(self.buttonBox)

        self.setLayout(dialogLayoutVMain)

        self.testsBereinigenUndListWidgetAusfuellen()
        # LineEdits befüllen
        if len(self.testuebernahmen) > 0:
            i = 0
            for kriterium in self.testuebernahmen[i].eindeutigkeitskriterien:
                if i < self.maxeindeutigkeitskriterien:
                    self.lineEditFeldkennungen[i].setText(kriterium)
                    self.lineEditKriterien[i].setText(self.testuebernahmen[0].eindeutigkeitskriterien[kriterium])
                i += 1
            self.lineEditPlatzhalterName.setText(self.testuebernahmen[0].platzhalterName)
            self.lineEditPlatzhalterFeldkennung.setText(self.testuebernahmen[0].platzhalterFeldkennung)
            self.listWidgetTestuebernahmen.setCurrentRow(0)
        
        self.testuebernahmeEntfernenAction.setEnabled(False)
    
    def getTestuebernahmeIndex(self, platzhalterName:str) -> int:
        """
        Gibt den Index aus self.testuebernahmen von Testübernahme mit angegebenem Platzhalternamen zurück
        Parameter:
            platzhalterName:str
        Return:
            Index:int, -1 falls nicht definiert
        """
        index = 0
        for testuebernahme in self.testuebernahmen:
            if testuebernahme.platzhalterName == platzhalterName:
                return index
            index += 1
        if index == len(self.testuebernahmen):
            index = -1
        return index

    def testsBereinigenUndListWidgetAusfuellen(self):
        self.listWidgetTestuebernahmen.clear()
        # Bereinigen
        i = 0
        for testuebernahme in self.testuebernahmen:
            if testuebernahme.platzhalterFeldkennung == "" and testuebernahme.platzhalterName == "" and len(testuebernahme.eindeutigkeitskriterien) == 0:
                self.testuebernahmen.pop(i)
            i += 1
        # Ausfüllen
        for testuebernahme in self.testuebernahmen:
            self.listWidgetTestuebernahmen.addItem(testuebernahme.platzhalterName)

    def pushButtonVariableClicked(self, checked, lineEditFeldkennung:QLineEdit, lineEditKriterium:QLineEdit):
        einfuegenOk = True
        if lineEditFeldkennung.text() != "" and self.comboBoxTextVariable.currentText()[:4] != lineEditFeldkennung.text():
            mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Die Feldkennung der einzufügenden Variable stimmt nicht mit der angegebenen Feldkennung überein.\nSoll die Variable dennoch eingefügt werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            mb.setDefaultButton(QMessageBox.StandardButton.No)
            mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
            mb.button(QMessageBox.StandardButton.No).setText("Nein")
            if mb.exec() == QMessageBox.StandardButton.No:
                einfuegenOk = False
        if einfuegenOk:
            if lineEditFeldkennung.text() == "":
                lineEditFeldkennung.setText(self.comboBoxTextVariable.currentText()[:4])
            bisherigerInhalt = lineEditKriterium.text()
            cursorPosition = lineEditKriterium.cursorPosition()
            variable = "${FK" + self.comboBoxTextVariable.currentText()[:4] + "}"
            neuerInhalt = bisherigerInhalt[:cursorPosition] + variable + bisherigerInhalt[cursorPosition:]
            lineEditKriterium.setText(neuerInhalt)
            lineEditKriterium.setFocus()
            lineEditKriterium.setCursorPosition(cursorPosition + len(variable))

    def pushButtonTextClicked(self, checked, lineEditFeldkennung:QLineEdit, lineEditKriterium:QLineEdit):
        einfuegenOk = True
        if lineEditFeldkennung.text() != "" and self.comboBoxTextVariable.currentText()[:4] != lineEditFeldkennung.text():
            mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Die Feldkennung des einzufügenden Texts stimmt nicht mit der angegebenen Feldkennung überein.\nSoll der Text dennoch eingefügt werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            mb.setDefaultButton(QMessageBox.StandardButton.No)
            mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
            mb.button(QMessageBox.StandardButton.No).setText("Nein")
            if mb.exec() == QMessageBox.StandardButton.No:
                einfuegenOk = False
        if einfuegenOk:
            if lineEditFeldkennung.text() == "":
                lineEditFeldkennung.setText(self.comboBoxTextVariable.currentText()[:4])
            bisherigerInhalt = lineEditKriterium.text()
            cursorPosition = lineEditKriterium.cursorPosition()
            text = self.comboBoxTextVariable.currentText()[6:]
            neuerInhalt = bisherigerInhalt[:cursorPosition] + text + bisherigerInhalt[cursorPosition:]
            lineEditKriterium.setText(neuerInhalt)
            lineEditKriterium.setFocus()
            lineEditKriterium.setCursorPosition(cursorPosition + len(text))

    def pushButtonTestuebernahmeHinzufuegenClicked(self):
        test = class_gdtdatei.Test("xxxx")
        eindeutigkeitsFeldkennungen = []
        keineFehler = False
        ueberschreiben = False
        unzulässigeFeldkennung = -1
        for i in range(self.maxeindeutigkeitskriterien):
            feldkennung = self.lineEditFeldkennungen[i].text()
            if feldkennung != "":
                kriterium = self.gdtDateiOptimiert.replaceFkVariablen(self.lineEditKriterien[i].text())
                if re.match(reFeldkennung, feldkennung) != None:
                    try:
                        test.setZeile(feldkennung, kriterium)
                        eindeutigkeitsFeldkennungen.append(feldkennung)
                    except class_gdtdatei.GdtFehlerException as e:
                        mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", e.meldung, QMessageBox.StandardButton.Ok)
                        mb.exec()
                        unzulässigeFeldkennung = i
        if unzulässigeFeldkennung == -1:
            test.setEindeutigkeitsFeldkennungen(eindeutigkeitsFeldkennungen)
            anzahlGefundeneTests = 0
            for prueftest in self.gdtDateiOptimiert.getTests():
                if test == prueftest:
                    anzahlGefundeneTests += 1
            listWidgetItemTexte = [self.listWidgetTestuebernahmen.item(i).text() for i in range(self.listWidgetTestuebernahmen.count())]
            if anzahlGefundeneTests == 0:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Es existiert kein Test mit den angegebenen Eindeutigkeitskriterien.", QMessageBox.StandardButton.Ok)
                mb.exec()
            elif anzahlGefundeneTests > 1:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Es existieren mehr als ein Test mit den angegebenen Eindeutigkeitskriterien.", QMessageBox.StandardButton.Ok)
                mb.exec()
            elif self.lineEditPlatzhalterName.text().strip() == "":
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Kein Platzhaltername eingetragen.", QMessageBox.StandardButton.Ok)
                mb.exec()
                self.lineEditPlatzhalterName.setFocus()
                self.lineEditPlatzhalterName.selectAll()
            elif self.lineEditPlatzhalterName.text() in listWidgetItemTexte:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Der angegebene Platzhaltername existiert bereits. Soll die Testübernahme überschrieben werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    keineFehler = True
                    ueberschreiben = True
                self.lineEditPlatzhalterName.setFocus()
                self.lineEditPlatzhalterName.selectAll()
            elif self.lineEditPlatzhalterFeldkennung.text().strip() == "":
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Keine Platzhalterfeldkennung eingetragen.", QMessageBox.StandardButton.Ok)
                mb.exec()
                self.lineEditPlatzhalterFeldkennung.setFocus()
                self.lineEditPlatzhalterFeldkennung.selectAll()
            elif re.match(reFeldkennung, self.lineEditPlatzhalterFeldkennung.text()) == None or self.lineEditPlatzhalterFeldkennung.text()[0:2] != "84" or self.lineEditPlatzhalterFeldkennung.text()[0:2] == "8410":
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Die angegebene Platzhalterfeldkennung ist ungültig.", QMessageBox.StandardButton.Ok)
                mb.exec()
                self.lineEditPlatzhalterFeldkennung.setFocus()
                self.lineEditPlatzhalterFeldkennung.selectAll()
            else:
                keineFehler = True
            if keineFehler: # Kriterien eindeutig
                eindeutigkeitskriterien = {}
                for i in range(self.maxeindeutigkeitskriterien):
                    feldkennung = self.lineEditFeldkennungen[i].text()
                    kriterium = self.lineEditKriterien[i].text()
                    if feldkennung != "":
                        eindeutigkeitskriterien[feldkennung] = kriterium
                testuebernahme = Testuebernahme(self.lineEditPlatzhalterName.text(), self.lineEditPlatzhalterFeldkennung.text(), eindeutigkeitskriterien)
                if ueberschreiben:
                    self.testuebernahmen[self.getTestuebernahmeIndex(self.lineEditPlatzhalterName.text())] = testuebernahme
                else:
                    self.testuebernahmen.append(testuebernahme)
                self.testsBereinigenUndListWidgetAusfuellen()
        else:
            self.lineEditFeldkennungen[unzulässigeFeldkennung].setFocus()
            self.lineEditFeldkennungen[unzulässigeFeldkennung].selectAll()


    def pushButtonUebernahmeEinfuegenClicked(self):
        if len(self.listWidgetTestuebernahmen.selectedItems()) == 0:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Keine Testübernahme ausgewählt.", QMessageBox.StandardButton.Ok)
            mb.exec()
        else:
            platzhalterName = self.listWidgetTestuebernahmen.currentItem().text()
            bisherigerInhalt = self.lineEditBefundzeile.text()
            cursorPosition = self.lineEditBefundzeile.cursorPosition()
            variable = "${" + platzhalterName + "}"
            neuerInhalt = bisherigerInhalt[:cursorPosition] + variable + bisherigerInhalt[cursorPosition:]
            self.lineEditBefundzeile.setText(neuerInhalt)
            self.lineEditBefundzeile.setFocus()
            self.lineEditBefundzeile.setCursorPosition(cursorPosition + len(variable))

    def listWidgetTestuebernahmeItemChanged(self,current):
        self.testuebernahmeEntfernenAction.setEnabled(self.listWidgetTestuebernahmen.currentItem() != None)
        platzhalterName = current.text()
        index = self.getTestuebernahmeIndex(platzhalterName)
        for i in range(self.maxeindeutigkeitskriterien):    
            self.lineEditFeldkennungen[i].setText("")
            self.lineEditKriterien[i].setText("")
        i = 0
        for kriterium in self.testuebernahmen[index].eindeutigkeitskriterien:
            self.lineEditFeldkennungen[i].setText(kriterium)
            self.lineEditKriterien[i].setText(self.testuebernahmen[index].eindeutigkeitskriterien[kriterium])
            i += 1
        self.lineEditPlatzhalterName.setText(self.testuebernahmen[index].platzhalterName)
        self.lineEditPlatzhalterFeldkennung.setText(self.testuebernahmen[index].platzhalterFeldkennung)

    def testuebernahmeEntfernen(self):
        currentRow = self.listWidgetTestuebernahmen.currentIndex().row()
        mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Soll die ausgewählte Testübernahme entfernt werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
        mb.button(QMessageBox.StandardButton.No).setText("Nein")
        if mb.exec() == QMessageBox.StandardButton.Yes:
            index = self.getTestuebernahmeIndex(self.listWidgetTestuebernahmen.currentItem().text())
            self.testuebernahmen.pop(index)
            self.testsBereinigenUndListWidgetAusfuellen()
            self.listWidgetTestuebernahmen.setCurrentRow(currentRow)

    def accept(self):
            self.done(1)
