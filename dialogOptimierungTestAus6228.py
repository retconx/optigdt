import re
import  class_gdtdatei
from PySide6.QtGui import Qt, QFont, QColor
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QGroupBox,
    QLineEdit,
    QMessageBox,
    QLabel,
    QComboBox
)

reFeldkennung = r"^\d{4}$"

class OptimierungTestAus6228(QDialog):
    def __init__(self, gdtDateiOriginal:class_gdtdatei.GdtDatei, trennRegexPattern:str, erkennungstext:str, erkennungsspalte:int, ergebnisspalte:int, testIdent:str, testBezeichnung:str, testEinheit:str, standard6228Trennzeichen:str, maxAnzahl6228Spalten:int):
        super().__init__()
        self.gdtDateiOriginal = gdtDateiOriginal
        self.trennRegexPattern = trennRegexPattern
        if trennRegexPattern == "":
            self.trennRegexPattern = standard6228Trennzeichen
        self.erkennungstext = erkennungstext
        self.erkennungsspalte = erkennungsspalte
        self.ergebnisspalte = ergebnisspalte
        self.testIdent = testIdent
        self.testBezeichnung = testBezeichnung
        self.testEinheit = testEinheit
        self.maxAnzahl6228Spalten = maxAnzahl6228Spalten
        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)
        self.fontGross = QFont()
        self.fontGross.setPixelSize(16)

        # ComboBox-Index berechnen
        index = 0
        for inhalt6228 in self.gdtDateiOriginal.get6228s(self.trennRegexPattern):
            if self.erkennungsspalte < len(inhalt6228) and inhalt6228[self.erkennungsspalte] == self.erkennungstext:
                break
            index += 1
        self.comboBoxIndex = index
        self.setWindowTitle("GDT-Optimierung: Test aus 6228-Zeile")
        self.setMinimumWidth(500)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type:ignore
        self.buttonBox.rejected.connect(self.reject) # type:ignore

        dialogLayoutV = QVBoxLayout()
        dialogLayoutG = QGridLayout()
        groupBox6228Erkennung = QGroupBox("6228-Erkennung")
        groupBox6228Erkennung.setFont(self.fontBold)
        groupBox6228Erkennung.setLayout(dialogLayoutG)
        self.comboBox6228 = QComboBox()
        self.comboBox6228.setFont(self.fontNormal)
        for zeile in self.gdtDateiOriginal.getZeilen():
            if zeile[3:7] == "6228":
                self.comboBox6228.addItem(zeile[7:].replace(" ", "\u2423")) # xxx
        label6228Zeile = QLabel("6228-Zeile:")
        label6228Zeile.setFont(self.fontNormal)
        labelAufteilung = QLabel("Aufteilung")
        labelAufteilung.setFont(self.fontNormal)
        label6228Spalten = []
        self.lineEdit6228Spalten = []
        for i in range(self.maxAnzahl6228Spalten):
            label6228Spalten.append(QLabel("Spalte " + str(i)))
            label6228Spalten[i].setFont(self.fontNormal)
            self.lineEdit6228Spalten.append(QLineEdit())
            self.lineEdit6228Spalten[i].setFont(self.fontNormal)
            self.lineEdit6228Spalten[i].setReadOnly(True)
        labelTrennzeichen = QLabel("Trennzeichen")
        labelTrennzeichen.setFont(self.fontNormal)
        self.lineEditTrennRegexPattern = QLineEdit(self.trennRegexPattern)
        self.lineEditTrennRegexPattern.setFont(self.fontNormal)
        self.lineEditTrennRegexPattern.textEdited.connect(self.lineEditPruefung) # type: ignore
        labelErkennungstext = QLabel("Erkennungstext")
        labelErkennungstext.setFont(self.fontNormal)
        self.lineEditErkennungstext = QLineEdit(self.erkennungstext)
        self.lineEditErkennungstext.setFont(self.fontNormal)
        self.lineEditErkennungstext.textEdited.connect(self.lineEditPruefung) # type: ignore
        labelErkennungsspalte = QLabel("Erkennungsspalte")
        labelErkennungsspalte.setFont(self.fontNormal)
        self.lineEditErkennungsspalte = QLineEdit(str(self.erkennungsspalte))
        self.lineEditErkennungsspalte.setFont(self.fontNormal)
        self.lineEditErkennungsspalte.textEdited.connect(self.lineEditPruefung) # type: ignore
        labelErkennungEindeutig = QLabel("Erkennung eindeutig")
        labelErkennungEindeutig.setFont(self.fontNormal)
        self.labelHaekchen = QLabel()
        self.labelHaekchen.setFont(self.fontGross)
        dialogLayoutG.addWidget(label6228Zeile, 0, 0, 1, 2)
        dialogLayoutG.addWidget(self.comboBox6228, 1, 0, 1, self.maxAnzahl6228Spalten + 1)
        dialogLayoutG.addWidget(labelAufteilung, 2, 0, 1, 1)
        for i in range(self.maxAnzahl6228Spalten):
            dialogLayoutG.addWidget(label6228Spalten[i], 2, (i + 1), 1, 1)
            dialogLayoutG.addWidget(self.lineEdit6228Spalten[i], 3, (i + 1), 1, 1)
        dialogLayoutG.addWidget(labelTrennzeichen, 4, 0, 1, 1)
        dialogLayoutG.addWidget(self.lineEditTrennRegexPattern, 4, 1, 1, self.maxAnzahl6228Spalten)
        dialogLayoutG.addWidget(labelErkennungstext, 5, 0, 1, 1)
        dialogLayoutG.addWidget(self.lineEditErkennungstext, 5, 1, 1, self.maxAnzahl6228Spalten)
        dialogLayoutG.addWidget(labelErkennungsspalte, 6, 0, 1, 1)
        dialogLayoutG.addWidget(self.lineEditErkennungsspalte, 6, 1, 1, self.maxAnzahl6228Spalten)
        dialogLayoutG.addWidget(labelErkennungEindeutig, 7, 0, 1, 1)
        dialogLayoutG.addWidget(self.labelHaekchen, 7, 1, 1, self.maxAnzahl6228Spalten)

        dialogLayoutG = QGridLayout()
        groupBoxTestDefinition = QGroupBox("Test-Definition")
        groupBoxTestDefinition.setFont(self.fontBold)
        groupBoxTestDefinition.setLayout(dialogLayoutG)
        labelErgebnisspalte = QLabel("Ergebnisspalte")
        labelErgebnisspalte.setFont(self.fontNormal)
        self.lineEditErgebnisspalte = QLineEdit(str(self.ergebnisspalte))
        self.lineEditErgebnisspalte.setFont(self.fontNormal)
        self.lineEditErgebnisspalte.textEdited.connect(self.lineEditPruefung) # type: ignore
        labelTestIdent = QLabel("Test-Ident")
        labelTestIdent.setFont(self.fontNormal)
        self.lineEditTestIdent = QLineEdit(self.testIdent)
        self.lineEditTestIdent.setFont(self.fontNormal)
        labelTestBezeichnung = QLabel("Test-Bezeichnung")
        labelTestBezeichnung.setFont(self.fontNormal)
        self.lineEditTestBezeichnung = QLineEdit(str(self.testBezeichnung))
        self.lineEditTestBezeichnung.setFont(self.fontNormal)
        labelTestEinheit = QLabel("Test-Einheit")
        labelTestEinheit.setFont(self.fontNormal)
        self.lineEditTestEinheit = QLineEdit(str(self.testEinheit))
        self.lineEditTestEinheit.setFont(self.fontNormal)
        dialogLayoutG.addWidget(labelErgebnisspalte, 0, 0, 1, 1)
        dialogLayoutG.addWidget(self.lineEditErgebnisspalte, 0, 1, 1, 1)
        dialogLayoutG.addWidget(labelTestIdent, 1, 0, 1, 1)
        dialogLayoutG.addWidget(self.lineEditTestIdent, 1, 1, 1, 1)
        dialogLayoutG.addWidget(labelTestBezeichnung, 2, 0, 1, 1)
        dialogLayoutG.addWidget(self.lineEditTestBezeichnung, 2, 1, 1, 1)
        dialogLayoutG.addWidget(labelTestEinheit, 3, 0, 1, 1)
        dialogLayoutG.addWidget(self.lineEditTestEinheit, 3, 1, 1, 1)

        dialogLayoutV.addWidget(groupBox6228Erkennung)
        dialogLayoutV.addWidget(groupBoxTestDefinition)
        dialogLayoutV.addWidget(self.buttonBox)
        self.setLayout(dialogLayoutV)

        self.setErkennungEindeutig(False)
        self.comboBox6228.currentTextChanged.connect(self.lineEditPruefung) # type: ignore
        self.comboBox6228.setCurrentIndex(self.comboBoxIndex)

    def setErkennungEindeutig(self, eindeutig:bool):
        if eindeutig:
            self.labelHaekchen.setText("\u2713")
            self.labelHaekchen.setStyleSheet("color:rgb(0,150,0)")
        else:
            self.labelHaekchen.setText("\u2715")
            self.labelHaekchen.setStyleSheet("color:rgb(150,0,0)")

    def erkennungIsEindeutig(self):
        return self.labelHaekchen.text() == "\u2713"
    
    def setErkennungshintergrund(self, spalte:int):
        for i in range(self.maxAnzahl6228Spalten):
            if self.lineEditErgebnisspalte.text() != "" and i != int(self.lineEditErgebnisspalte.text()):
                self.lineEdit6228Spalten[i].setStyleSheet("background:rgb(255,255,255)")
        if spalte < self.maxAnzahl6228Spalten:
            self.lineEdit6228Spalten[spalte].setStyleSheet("background:rgb(220,255,220)")

    def setErgebnisshintergrund(self, spalte:int):
        for i in range(self.maxAnzahl6228Spalten):
            if self.lineEditErkennungsspalte.text() != "" and i != int(self.lineEditErkennungsspalte.text()):
                self.lineEdit6228Spalten[i].setStyleSheet("background:rgb(255,255,255)")
        if spalte < self.maxAnzahl6228Spalten:
            self.lineEdit6228Spalten[spalte].setStyleSheet("background:rgb(220,220,255)")

    def lineEditPruefung(self):
        regexPattern = self.lineEditTrennRegexPattern.text()
        aufgeteilteZeile = re.split(regexPattern, self.comboBox6228.currentText().replace("\u2423", " ")) # xxx
        for i in range(self.maxAnzahl6228Spalten):
            if i < len(aufgeteilteZeile):
                self.lineEdit6228Spalten[i].setText(aufgeteilteZeile[i].replace(" ", "\u2423"))
            else:
                self.lineEdit6228Spalten[i].setText("")
        gefundene6228s = 0
        for inhalt6228 in self.gdtDateiOriginal.get6228s(regexPattern):
            if self.lineEditErkennungsspalte.text() != "" and int(self.lineEditErkennungsspalte.text()) < len(inhalt6228) and inhalt6228[int(self.lineEditErkennungsspalte.text())] == self.lineEditErkennungstext.text():
                gefundene6228s += 1
        self.setErkennungEindeutig(gefundene6228s == 1 and re.split(regexPattern, self.comboBox6228.currentText().replace("\u2423", " "))[int(self.lineEditErkennungsspalte.text())] == self.lineEditErkennungstext.text()) # xxx
        if self.lineEditErkennungsspalte.text() != "":
            self.setErkennungshintergrund(int(self.lineEditErkennungsspalte.text()))
        if self.lineEditErgebnisspalte.text() != "":
            self.setErgebnisshintergrund(int(self.lineEditErgebnisspalte.text()))

    def accept(self):
        fehler = []
        if not self.erkennungIsEindeutig():
            fehler.append("6228-Erkennung ist nicht eindeutig.")
        if self.lineEditErkennungsspalte.text() == self.lineEditErgebnisspalte.text():
            fehler.append("Erkennungsspalte und Ergebnisspalte dürfen nicht gleich sein.")
        if self.lineEditErgebnisspalte.text() == "":
            fehler.append("Keine Ergebnisspalte eingetragen.")
        elif int(self.lineEditErgebnisspalte.text()) < 0 or int(self.lineEditErgebnisspalte.text()) >= self.maxAnzahl6228Spalten:
            fehler.append("Ergebnisspalte ist ungültig.")
        alleTestIdents = self.gdtDateiOriginal.getInhalte("8410")
        testIdentIsEindeutig = self.lineEditTestIdent.text() not in alleTestIdents
        if not testIdentIsEindeutig:
            fehler.append("Test-Ident ist nicht eindeutig.")
        if self.lineEditTestBezeichnung.text() == "":
            fehler.append("Keine Test-Bezeichnung eingetragen.")
        if len(fehler) == 0:
            self.done(1)
        else:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Formular nicht korrekt ausgefüllt:\n- " + "\n- ".join(fehler), QMessageBox.StandardButton.Ok)
            mb.exec()