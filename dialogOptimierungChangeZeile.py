import re
import  class_gdtdatei
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QLineEdit,
    QCheckBox,
    QLabel,
    QComboBox,
    QPushButton
)

reFeldkennung = r"^\d{4}$"

class OptimierungChangeZeile(QDialog):
    def __init__(self, gdtDateiOriginal:class_gdtdatei.GdtDatei, alleVorkommen:bool=False, feldkennung:str="", neuerInhalt:str=""):
        super().__init__()
        self.gdtDateiOriginal = gdtDateiOriginal
        self.alleVorkommen = alleVorkommen
        self.feldkennung = feldkennung
        self.neuerInhalt = neuerInhalt
        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontNormal.setItalic(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)
        self.fontBoldItalic = QFont()
        self.fontBoldItalic.setBold(True)
        self.fontBoldItalic.setItalic(True)

        self.setWindowTitle("GDT-Optimierung: Zeile ändern")
        self.setMinimumWidth(400)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type:ignore
        self.buttonBox.rejected.connect(self.reject) # type:ignore

        dialogLayoutV = QVBoxLayout()
        dialogLayoutG = QGridLayout()
        groupBoxZeileAendern = QGroupBox("Zu ändernde Zeile")
        groupBoxZeileAendern.setFont(self.fontBold)
        groupBoxZeileAendern.setLayout(dialogLayoutG)
        labelFeldkennung = QLabel("Zeile")
        labelFeldkennung.setFont(self.fontNormal)
        self.comboBoxZeile = QComboBox()
        self.comboBoxZeile.setFont(self.fontNormal)
        self.comboBoxZeile.setEditable(False)
        self.comboBoxZeile.setFixedWidth(300)
        i = 0
        for zeile in gdtDateiOriginal.getZeilen():
            self.comboBoxZeile.addItem(zeile[3:7] + ": " + zeile[7:])
            i += 1
        labelNeuerInhalt = QLabel("Neuer Inhalt")
        labelNeuerInhalt.setFont(self.fontNormal)
        self.lineEditNeuerInhalt = QLineEdit(self.neuerInhalt)
        self.lineEditNeuerInhalt.setFont(self.fontNormal)
        self.lineEditNeuerInhalt.setPlaceholderText("z. B. Körpergröße: ${FK3622}")
        self.pushButtonText = QPushButton("T")
        self.pushButtonText.setFont(self.fontNormal)
        self.pushButtonText.setToolTip("Text einfügen")
        self.pushButtonText.clicked.connect(lambda checked = False, lineEditInhalt = self.lineEditNeuerInhalt: self.pushButtonTextClicked(checked, lineEditInhalt)) # type: ignore
        self.pushButtonVariable = QPushButton("V")
        self.pushButtonVariable.setFont(self.fontNormal)
        self.pushButtonVariable.setToolTip("Variable einfügen")
        self.pushButtonVariable.clicked.connect(lambda checked = False, lineEditInhalt = self.lineEditNeuerInhalt: self.pushButtonVariableClicked(checked, lineEditInhalt)) # type: ignore
        self.checkBoxAlle = QCheckBox("Alle Zeilen")
        self.checkBoxAlle.setFont(self.fontNormal)
        self.checkBoxAlle.setChecked(self.alleVorkommen)
        dialogLayoutG.addWidget(labelFeldkennung, 0, 0)
        dialogLayoutG.addWidget(self.comboBoxZeile, 0, 1, 1, 3)
        dialogLayoutG.addWidget(labelNeuerInhalt, 1, 0)
        dialogLayoutG.addWidget(self.lineEditNeuerInhalt, 1, 1, 1, 1)
        dialogLayoutG.addWidget(self.pushButtonText, 1, 2, 1, 1)
        dialogLayoutG.addWidget(self.pushButtonVariable, 1, 3, 1, 1)
        
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
        dialogLayoutG.addWidget(groupBoxTextVariableEinfuegen, 2, 0, 1, 4)
        dialogLayoutG.addWidget(self.checkBoxAlle, 3, 0, 1, 4)

        dialogLayoutV.addWidget(groupBoxZeileAendern)
        dialogLayoutV.addWidget(self.buttonBox)

        self.setLayout(dialogLayoutV)

    def pushButtonTextClicked(self, checked, lineEdit:QLineEdit):
        bisherigerInhalt = lineEdit.text()
        cursorPosition = lineEdit.cursorPosition()
        text = self.comboBoxTextVariable.currentText()[6:]
        neuerInhalt = bisherigerInhalt[:cursorPosition] + text + bisherigerInhalt[cursorPosition:]
        lineEdit.setText(neuerInhalt)
        lineEdit.setCursorPosition(cursorPosition + len(text))
        
    def pushButtonVariableClicked(self, checked, lineEdit:QLineEdit):
        bisherigerInhalt = lineEdit.text()
        cursorPosition = lineEdit.cursorPosition()
        variable = "${FK" + self.comboBoxTextVariable.currentText()[:4] + "}"
        neuerInhalt = bisherigerInhalt[:cursorPosition] + variable + bisherigerInhalt[cursorPosition:]
        lineEdit.setText(neuerInhalt)
        lineEdit.setCursorPosition(cursorPosition + len(variable))