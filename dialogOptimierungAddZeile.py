import re
import  class_gdtdatei, class_Enums
from PySide6.QtGui import QFont
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

class OptimierungAddZeile(QDialog):
    def __init__(self, gdtDateiOriginal:class_gdtdatei.GdtDatei, feldkennung:str, inhalt:str, zeileEinfuegen:class_Enums.ZeileEinfuegen):
        super().__init__()
        self.gdtDateiOriginal = gdtDateiOriginal
        self.feldkennung = feldkennung
        self.inhalt = inhalt
        self.zeileEinfuegen = zeileEinfuegen
        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontNormal.setItalic(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)
        self.fontBoldItalic = QFont()
        self.fontBoldItalic.setBold(True)
        self.fontBoldItalic.setItalic(True)

        self.setWindowTitle("GDT-Optimierung: Zeile hinzufügen")
        self.setMinimumWidth(400)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type:ignore
        self.buttonBox.rejected.connect(self.reject) # type:ignore

        dialogLayoutV = QVBoxLayout()
        dialogLayoutG = QGridLayout()
        groupBoxZeileHinzufuegen = QGroupBox("Hinzuzfügende Zeile")
        groupBoxZeileHinzufuegen.setFont(self.fontBold)
        groupBoxZeileHinzufuegen.setLayout(dialogLayoutG)
        labelFeldkennung = QLabel("Feldkennung")
        labelFeldkennung.setFont(self.fontNormal)
        self.lineEditFeldkennung = QLineEdit(self.feldkennung)
        self.lineEditFeldkennung.setFont(self.fontNormal)
        self.lineEditFeldkennung.setPlaceholderText("z. B. 6227")
        labelInhalt = QLabel("Inhalt")
        labelInhalt.setFont(self.fontNormal)
        self.lineEditInhalt = QLineEdit(self.inhalt)
        self.lineEditInhalt.setFont(self.fontNormal)
        self.lineEditInhalt.setPlaceholderText("z. B. Körpergröße: ${FK3622}")
        self.pushButtonText = QPushButton("T")
        self.pushButtonText.setFont(self.fontNormal)
        self.pushButtonText.setToolTip("Text einfügen")
        self.pushButtonText.clicked.connect(lambda checked = False, lineEditInhalt = self.lineEditInhalt: self.pushButtonTextClicked(checked, lineEditInhalt)) # type: ignore
        self.pushButtonVariable = QPushButton("V")
        self.pushButtonVariable.setFont(self.fontNormal)
        self.pushButtonVariable.setToolTip("Variable einfügen")
        self.pushButtonVariable.clicked.connect(lambda checked = False, lineEditInhalt = self.lineEditInhalt: self.pushButtonVariableClicked(checked, lineEditInhalt)) # type: ignore
        einfuegenLayoutH =QHBoxLayout()
        labelEinfuegen = QLabel("Einfügen")
        labelEinfuegen.setFont(self.fontNormal)
        self.comboBoxVorNach = QComboBox()
        self.comboBoxVorNach.addItems(["vor", "nach"])
        self.comboBoxVorNach.setFont(self.fontNormal)
        self.comboBoxVorNach.setCurrentIndex(self.zeileEinfuegen.vorNach)
        self.lineEditVorkommen = QLineEdit(str(self.zeileEinfuegen.vorkommen))
        self.lineEditVorkommen.setFont(self.fontNormal)
        labelPunkt = QLabel(". Vorkommen von Feldkennung")
        labelPunkt.setFont(self.fontNormal)
        self.lineEditEinfuegenFeldkennung = QLineEdit(self.zeileEinfuegen.feldkennung)
        self.lineEditEinfuegenFeldkennung.setFont(self.fontNormal)
        einfuegenLayoutH.addWidget(labelEinfuegen)
        einfuegenLayoutH.addWidget(self.comboBoxVorNach)
        einfuegenLayoutH.addWidget(self.lineEditVorkommen)
        einfuegenLayoutH.addWidget(labelPunkt)
        einfuegenLayoutH.addWidget(self.lineEditEinfuegenFeldkennung)
        dialogLayoutG.addWidget(labelFeldkennung, 0, 0)
        dialogLayoutG.addWidget(self.lineEditFeldkennung, 0, 1, 1, 3)
        dialogLayoutG.addWidget(labelInhalt, 1, 0)
        dialogLayoutG.addWidget(self.lineEditInhalt, 1, 1, 1, 1)
        dialogLayoutG.addWidget(self.pushButtonText, 1, 2, 1, 1)
        dialogLayoutG.addWidget(self.pushButtonVariable, 1, 3, 1, 1)
        dialogLayoutG.addLayout(einfuegenLayoutH, 2, 0, 1, 4)
        
        dialogLayoutH = QHBoxLayout()
        groupBoxTextVariableEinfuegen = QGroupBox("Als Text (T) oder Variable (V) einfügen")
        groupBoxTextVariableEinfuegen.setFont(self.fontBoldItalic)
        groupBoxTextVariableEinfuegen.setLayout(dialogLayoutH)
        labelTextVariable = QLabel("Verfügbare Feldkennungen/Inhalte")
        labelTextVariable.setFont(self.fontNormal)
        self.comboBoxTextVariable = QComboBox()
        self.comboBoxTextVariable.setFont(self.fontNormal)
        self.comboBoxTextVariable.setEditable(False)
        self.comboBoxTextVariable.setFixedWidth(300)
        i = 0
        for zeile in gdtDateiOriginal.getZeilen():
            self.comboBoxTextVariable.addItem(zeile[3:7] + ": " + zeile[7:])
            i += 1
        dialogLayoutH.addWidget(labelTextVariable)
        dialogLayoutH.addWidget(self.comboBoxTextVariable)
        dialogLayoutG.addWidget(groupBoxTextVariableEinfuegen, 3, 0, 1, 4)

        dialogLayoutV.addWidget(groupBoxZeileHinzufuegen)
        dialogLayoutV.addWidget(self.buttonBox)

        self.setLayout(dialogLayoutV)
        self.lineEditFeldkennung.setFocus()
        self.lineEditFeldkennung.selectAll()

    def pushButtonTextClicked(self, checked, lineEdit:QLineEdit):
        bisherigerInhalt = lineEdit.text()
        cursorPosition = lineEdit.cursorPosition()
        text = self.comboBoxTextVariable.currentText()[6:]
        neuerInhalt = bisherigerInhalt[:cursorPosition] + text + bisherigerInhalt[cursorPosition:]
        lineEdit.setText(neuerInhalt)
        lineEdit.setFocus()
        lineEdit.setCursorPosition(cursorPosition + len(text))
        
    def pushButtonVariableClicked(self, checked, lineEdit:QLineEdit):
        bisherigerInhalt = lineEdit.text()
        cursorPosition = lineEdit.cursorPosition()
        variable = "${FK" + self.comboBoxTextVariable.currentText()[:4] + "}"
        neuerInhalt = bisherigerInhalt[:cursorPosition] + variable + bisherigerInhalt[cursorPosition:]
        lineEdit.setText(neuerInhalt)
        lineEdit.setFocus()
        lineEdit.setCursorPosition(cursorPosition + len(variable))

    def accept(self):
        if self.lineEditFeldkennung.text() == "" and self.lineEditFeldkennung.text() == "":
            self.done(1)
        elif not re.match(reFeldkennung, self.lineEditFeldkennung.text()):
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Die Feldkennung muss aus vier Ziffern bestehen.", QMessageBox.StandardButton.Ok)
            mb.exec()
            self.lineEditFeldkennung.setFocus()
            self.lineEditFeldkennung.selectAll()
        elif self.lineEditEinfuegenFeldkennung.text() != "" and not re.match(reFeldkennung, self.lineEditEinfuegenFeldkennung.text()):
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Die Feldkennung muss aus vier Ziffern bestehen.", QMessageBox.StandardButton.Ok)
            mb.exec()
            self.lineEditEinfuegenFeldkennung.setFocus()
            self.lineEditEinfuegenFeldkennung.selectAll()
        elif self.lineEditEinfuegenFeldkennung.text() != "":
            korrekt = True
            if not re.match(r"^\d+$", self.lineEditVorkommen.text()):
                korrekt = False
            elif int(self.lineEditVorkommen.text()) == 0:
                korrekt = False
            if not korrekt:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Das Vorkommen muss eine Zahl > 0 sein.", QMessageBox.StandardButton.Ok)
                mb.exec()
                self.lineEditVorkommen.setFocus()
                self.lineEditVorkommen.selectAll()
            else:
                self.done(1)
        else:
            self.done(1)