import re
import  class_gdtdatei
from PySide6.QtGui import Qt, QFont
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
    QPushButton
)

reFeldkennung = r"^\d{4}$"

class OptimierungDeleteTest(QDialog):
    def __init__(self, gdtDateiOriginal:class_gdtdatei.GdtDatei, maxeindeutigkeitskriterien:int, eindeutigkeitskriterien:dict={}):
        super().__init__()
        self.gdtDateiOriginal = gdtDateiOriginal
        self.maxeindeutigkeitskriterien = maxeindeutigkeitskriterien
        self.eindeutigkeitskriterien = eindeutigkeitskriterien
        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontNormal.setItalic(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)
        self.fontBoldItalic = QFont()
        self.fontBoldItalic.setBold(True)
        self.fontBoldItalic.setItalic(True)

        self.setWindowTitle("GDT-Optimierung: Test entfernen")
        self.setMinimumWidth(500)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type:ignore
        self.buttonBox.rejected.connect(self.reject) # type:ignore

        dialogLayoutV = QVBoxLayout()
        dialogLayoutG = QGridLayout()
        groupBoxEindeutigkeitskriterien = QGroupBox("Eindeutigkeitskriterien")
        groupBoxEindeutigkeitskriterien.setFont(self.fontBold)
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
        # LineEdits befüllen
        i = 0
        for kriterium in self.eindeutigkeitskriterien:
            if i < self.maxeindeutigkeitskriterien:
                self.lineEditFeldkennungen[i].setText(kriterium)
                self.lineEditKriterien[i].setText(self.eindeutigkeitskriterien[kriterium])
            i += 1
        
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
        for zeile in self.gdtDateiOriginal.getZeilen():
            self.comboBoxTextVariable.addItem(zeile[3:7] + ": " + zeile[7:])
            i += 1
        dialogLayoutHTextVariable.addWidget(labelTextVariable)
        dialogLayoutHTextVariable.addWidget(self.comboBoxTextVariable)
        dialogLayoutG.addWidget(groupBoxTextVariableEinfuegen, (self.maxeindeutigkeitskriterien - 1) * 2 + 2, 0, 1, 4)

        dialogLayoutV.addWidget(groupBoxEindeutigkeitskriterien)
        dialogLayoutV.addWidget(self.buttonBox)

        self.setLayout(dialogLayoutV)
        self.lineEditFeldkennungen[0].setFocus()
        self.lineEditFeldkennungen[0].selectAll()

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

    def accept(self):
        feldkennungenOk = True
        kriterienOk = True
        for i in range(self.maxeindeutigkeitskriterien):
            if self.lineEditFeldkennungen[i].text() != "" and not re.match(reFeldkennung, self.lineEditFeldkennungen[i].text()):
                feldkennungenOk = False
                break
        if not feldkennungenOk:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Feldkennungen müssen aus vier Ziffern bestehen.", QMessageBox.StandardButton.Ok)
            mb.exec()
        else:
            self.eindeutigkeitskriterien.clear()
            test = class_gdtdatei.Test("xxxx")
            eindeutigkeitsFeldkennungen = []
            for i in range(self.maxeindeutigkeitskriterien):
                feldkennung = self.lineEditFeldkennungen[i].text()
                if feldkennung != "":
                    kriterium = self.gdtDateiOriginal.replaceFkVariablen(self.lineEditKriterien[i].text())
                    if re.match(reFeldkennung, feldkennung) != None:
                        test.setZeile(feldkennung, kriterium)
                        eindeutigkeitsFeldkennungen.append(feldkennung)
            test.setEindeutigkeitsFeldkennungen(eindeutigkeitsFeldkennungen)
            anzahlGefundeneTests = 0
            for prueftest in self.gdtDateiOriginal.getTests():
                if test == prueftest:
                    anzahlGefundeneTests += 1
            if anzahlGefundeneTests == 0:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Es existiert kein Test mit den angegebenen Eindeutigkeitskriterien.", QMessageBox.StandardButton.Ok)
                mb.exec()
            elif anzahlGefundeneTests > 1:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Es existieren mehr als ein Test mit den angegebenen Eindeutigkeitskriterien.", QMessageBox.StandardButton.Ok)
                mb.exec()
            elif anzahlGefundeneTests == 1:
                for i in range(self.maxeindeutigkeitskriterien):
                    feldkennung = self.lineEditFeldkennungen[i].text()
                    kriterium = self.lineEditKriterien[i].text()
                    if feldkennung != "" and kriterium != "":
                        self.eindeutigkeitskriterien[feldkennung] = kriterium
                self.done(1)