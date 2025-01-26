import re
import  class_gdtdatei
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QLineEdit,
    QMessageBox,
    QLabel,
    QPushButton
)

class ErgebnisAnpassen(QDialog):
    def __init__(self, testBezeichnung:str, angepassteErgebnisse:dict):
        super().__init__()
        self.testBezeichnung = testBezeichnung
        self.angepassteErgebnisseDict = angepassteErgebnisse
        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontNormal.setItalic(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)
        self.fontBoldItalic = QFont()
        self.fontBoldItalic.setBold(True)
        self.fontBoldItalic.setItalic(True)

        self.maximaleAnpassungen = 4

        self.setWindowTitle("Test-Ergebnis anpassen (" + self.testBezeichnung + ")")
        self.setMinimumWidth(400)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        dialogLayoutV = QVBoxLayout()
        self.dialogLayoutG = QGridLayout()
        labelOriginal = QLabel("Original")
        labelOriginal.setFont(self.fontBold)
        labelAngepasst = QLabel("Angepasst")
        labelAngepasst.setFont(self.fontBold)
        self.dialogLayoutG.addWidget(labelOriginal, 0, 0, 1, 1)
        self.dialogLayoutG.addWidget(labelAngepasst, 0, 1, 1, 1)
        self.lineEditErgebnisse = []
        self.lineEditAngepasste = []
        self.pushButtonLoeschen = []

        angepassteErgebnisseList = list(self.angepassteErgebnisseDict)
        for i in range(self.maximaleAnpassungen):
            tempLineEditErgebnis = QLineEdit()
            tempLineEditErgebnis.setFont(self.fontNormal)
            self.lineEditErgebnisse.append(tempLineEditErgebnis)
            tempLineEditAngepasst = QLineEdit()
            tempLineEditAngepasst.setFont(self.fontNormal)
            self.lineEditAngepasste.append(tempLineEditAngepasst)
            tempPushButtonLoeschen = QPushButton("\U0001f5d1")
            tempPushButtonLoeschen.setFont(self.fontNormal)
            tempPushButtonLoeschen.clicked.connect(lambda checked = False, buttonNr = i:self.buttonLoeschenClicked(checked, buttonNr))
            self.pushButtonLoeschen.append(tempPushButtonLoeschen)
            self.dialogLayoutG.addWidget(tempLineEditErgebnis, i + 1, 0, 1, 1)
            self.dialogLayoutG.addWidget(tempLineEditAngepasst, i + 1, 1, 1, 1)
            self.dialogLayoutG.addWidget(tempPushButtonLoeschen, i + 1, 2, 1, 1)
            if i < len(angepassteErgebnisseList):
                tempLineEditErgebnis.setText(angepassteErgebnisseList[i])
                tempLineEditAngepasst.setText(self.angepassteErgebnisseDict[angepassteErgebnisseList[i]])
            i += 1

        dialogLayoutV.addLayout(self.dialogLayoutG)
        dialogLayoutV.addWidget(self.buttonBox)

        self.setLayout(dialogLayoutV)
        self.lineEditAngepasste[0].setFocus()
        self.lineEditAngepasste[0].selectAll()

    def buttonLoeschenClicked(self, checked, buttonNr):
        self.lineEditErgebnisse[buttonNr].setText("")
        self.lineEditAngepasste[buttonNr].setText("")

    def accept(self):
        self.angepassteErgebnisseDict.clear()
        formularOk = True
        for i in range(self.maximaleAnpassungen):
            if self.lineEditErgebnisse[i].text() != "" and self.lineEditAngepasste[i].text() == "":
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", str(i + 1) + ". Zeile unvollständig ausgefüllt", QMessageBox.StandardButton.Ok)
                mb.exec()
                self.lineEditAngepasste[i].setFocus()
                formularOk = False
                break
            elif self.lineEditErgebnisse[i].text() == "" and self.lineEditAngepasste[i].text() != "":
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", str(i + 1) + ". Zeile unvollständig ausgefüllt", QMessageBox.StandardButton.Ok)
                mb.exec()
                self.lineEditErgebnisse[i].setFocus()
                formularOk = False
                break
            elif self.lineEditErgebnisse[i].text() != "" and self.lineEditAngepasste[i].text() != "":
                self.angepassteErgebnisseDict[self.lineEditErgebnisse[i].text()] = self.lineEditAngepasste[i].text()
        if formularOk:
            self.done(1)