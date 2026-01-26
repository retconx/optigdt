import os, re
import  class_gdtdatei, class_Enums, class_gdtdatei
from PySide6.QtGui import QFont, Qt
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
    QCheckBox
)

reFeldkennung = r"^\d{4}$"
reDezimalzahl = r"^\d+([.,]\d+)?$"

class OptimierungTestAusGgb(QDialog):
    def __init__(self, gdtDateiOptimiert:class_gdtdatei.GdtDatei, groesseTest:class_gdtdatei.Test, groesseZeileLoeschen:bool, gewichtTest:class_gdtdatei.Test, gewichtZeileLoeschen:bool, bmiTest:class_gdtdatei.Test):
        super().__init__()
        self.gdtDateiOptimiert = gdtDateiOptimiert
        self.groesseTest = groesseTest
        self.groesseZeileLoeschen = groesseZeileLoeschen
        self.gewichtTest = gewichtTest
        self.gewichtZeileLoeschen = gewichtZeileLoeschen
        self.bmiTest = bmiTest
        self.groesseFloat = 0
        self.gewichtFloat = 0
        # Einheiten berechnen
        if self.groesseTest.getInhalt("8420") != "":
            groesse = self.groesseTest.getInhalt("8420")
            self.groesseEinheitBerechnet = class_Enums.Einheit.M
            if re.match(reDezimalzahl, groesse) != None:
                self.groesseFloat = float(groesse.replace(",", ":"))
                if self.groesseFloat > 3:
                    self.groesseEinheitBerechnet = class_Enums.Einheit.CM
        if self.gewichtTest.getInhalt("8420") != "":
            gewicht = self.gewichtTest.getInhalt("8420")
            self.gewichtEinheitBerechnet = class_Enums.Einheit.KG
            if re.match(reDezimalzahl, gewicht) != None:
                self.gewichtFloat = float(gewicht.replace(",", ":"))
                if self.gewichtFloat > 500:
                    self.gewichtEinheitBerechnet = class_Enums.Einheit.G

        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontNormal.setItalic(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)
        self.fontBoldItalic = QFont()
        self.fontBoldItalic.setBold(True)
        self.fontBoldItalic.setItalic(True)
        self.fontKlein= QFont()
        self.fontKlein.setBold(False)
        self.fontKlein.setItalic(False)
        self.fontKlein.setPointSize(12)
        self.setMinimumWidth(400)

        self.setWindowTitle("GDT-Optimierung: Test aus Größe/Gewicht/BMI")
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) 
        self.buttonBox.rejected.connect(self.reject)

        dialogLayoutV = QVBoxLayout()
        dialogLayoutH = QHBoxLayout()

        self.groesseVorhanden = False
        self.gewichtVorhanden = False

        if self.groesseTest.getInhalt("8420") != "":
            self.groesseVorhanden = True
            groupBoxGroesseLayout = QGridLayout()
            groupBoxGroesse = QGroupBox("Größe")
            groupBoxGroesse.setFont(self.fontBold)
            labelGroesseTestIdent = QLabel("Test-Ident")
            labelGroesseTestIdent.setFont(self.fontNormal)
            self.lineEditGroesseTestIdent = QLineEdit(self.groesseTest.getInhalt("8410"))
            self.lineEditGroesseTestIdent.setFont(self.fontNormal)
            labelGroesseTestBezeichnung = QLabel("Test-Bezeichnung")
            labelGroesseTestBezeichnung.setFont(self.fontNormal)
            self.lineEditGroesseTestBezeichnung = QLineEdit(self.groesseTest.getInhalt("8411"))
            self.lineEditGroesseTestBezeichnung.setFont(self.fontNormal)
            labelGroesseTestErgebnis = QLabel("Test-Ergebnis")
            labelGroesseTestErgebnis.setFont(self.fontNormal)
            self.lineEditGroesseTestErgebnis = QLineEdit(self.groesseTest.getInhalt("8420").replace(".", ","))
            self.lineEditGroesseTestErgebnis.setFont(self.fontNormal)
            self.lineEditGroesseTestErgebnis.setReadOnly(True)
            self.labelGroesseEinheitBerechnet = QLabel(self.groesseEinheitBerechnet.value)
            self.labelGroesseEinheitBerechnet.setFont(self.fontNormal)
            labelGroesseTestEinheit = QLabel("Test-Einheit")
            labelGroesseTestEinheit.setFont(self.fontNormal)
            self.comboBoxGroesseTestEinheit = QComboBox()
            self.comboBoxGroesseTestEinheit.setFont(self.fontNormal)
            self.comboBoxGroesseTestEinheit.addItems([class_Enums.Einheit.CM.value, class_Enums.Einheit.M.value])
            self.comboBoxGroesseTestEinheit.setCurrentText(self.groesseEinheitBerechnet.value)
            self.comboBoxGroesseTestEinheit.currentTextChanged.connect(self.comboBoxGroesseTestEinheitChanged)
            self.checkBoxGroesseLoeschen = QCheckBox("Größe-Zeile löschen (Feldkennung 3622)")
            self.checkBoxGroesseLoeschen.setFont(self.fontNormal)
            self.checkBoxGroesseLoeschen.setChecked(self.groesseZeileLoeschen)

            groupBoxGroesseLayout.addWidget(labelGroesseTestIdent, 0, 0)
            groupBoxGroesseLayout.addWidget(self.lineEditGroesseTestIdent, 0, 1)
            groupBoxGroesseLayout.addWidget(labelGroesseTestBezeichnung, 1, 0)
            groupBoxGroesseLayout.addWidget(self.lineEditGroesseTestBezeichnung, 1, 1)
            groupBoxGroesseLayout.addWidget(labelGroesseTestErgebnis, 2, 0)
            groupBoxGroesseLayout.addWidget(self.lineEditGroesseTestErgebnis, 2, 1)
            groupBoxGroesseLayout.addWidget(self.labelGroesseEinheitBerechnet, 2, 2)
            groupBoxGroesseLayout.addWidget(labelGroesseTestErgebnis, 2, 0)
            groupBoxGroesseLayout.addWidget(self.lineEditGroesseTestErgebnis, 2, 1)
            groupBoxGroesseLayout.addWidget(self.labelGroesseEinheitBerechnet, 2, 2)
            groupBoxGroesseLayout.addWidget(labelGroesseTestEinheit, 3, 0)
            groupBoxGroesseLayout.addWidget(self.comboBoxGroesseTestEinheit, 3, 1)
            groupBoxGroesseLayout.addWidget(self.checkBoxGroesseLoeschen, 4, 0, 1, 2)
            groupBoxGroesse.setLayout(groupBoxGroesseLayout)
            dialogLayoutH.addWidget(groupBoxGroesse)

        if self.gewichtTest.getInhalt("8420") != "":
            self.gewichtVorhanden = True
            groupBoxGewichtLayout = QGridLayout()
            groupBoxGewicht = QGroupBox("Gewicht")
            groupBoxGewicht.setFont(self.fontBold)
            labelGewichtTestIdent = QLabel("Test-Ident")
            labelGewichtTestIdent.setFont(self.fontNormal)
            self.lineEditGewichtTestIdent = QLineEdit(self.gewichtTest.getInhalt("8410"))
            self.lineEditGewichtTestIdent.setFont(self.fontNormal)
            labelGewichtTestBezeichnung = QLabel("Test-Bezeichnung")
            labelGewichtTestBezeichnung.setFont(self.fontNormal)
            self.lineEditGewichtTestBezeichnung = QLineEdit(self.gewichtTest.getInhalt("8411"))
            self.lineEditGewichtTestBezeichnung.setFont(self.fontNormal)
            labelGewichtTestErgebnis = QLabel("Test-Ergebnis")
            labelGewichtTestErgebnis.setFont(self.fontNormal)
            self.lineEditGewichtTestErgebnis = QLineEdit(self.gewichtTest.getInhalt("8420").replace(".", ","))
            self.lineEditGewichtTestErgebnis.setFont(self.fontNormal)
            self.lineEditGewichtTestErgebnis.setReadOnly(True)
            self.labelGewichtEinheitBerechnet = QLabel(self.gewichtEinheitBerechnet.value)
            self.labelGewichtEinheitBerechnet.setFont(self.fontNormal)
            labelGewichtTestEinheit = QLabel("Test-Einheit")
            labelGewichtTestEinheit.setFont(self.fontNormal)
            self.comboBoxGewichtTestEinheit = QComboBox()
            self.comboBoxGewichtTestEinheit.setFont(self.fontNormal)
            self.comboBoxGewichtTestEinheit.addItems([class_Enums.Einheit.G.value, class_Enums.Einheit.KG.value])
            self.comboBoxGewichtTestEinheit.setCurrentText(self.gewichtEinheitBerechnet.value)
            self.comboBoxGewichtTestEinheit.currentTextChanged.connect(self.comboBoxGewichtTestEinheitChanged)
            self.checkBoxGewichtLoeschen = QCheckBox("Gewicht-Zeile löschen (Feldkennung 3623)")
            self.checkBoxGewichtLoeschen.setFont(self.fontNormal)
            self.checkBoxGewichtLoeschen.setChecked(self.gewichtZeileLoeschen)

            groupBoxGewichtLayout.addWidget(labelGewichtTestIdent, 0, 0)
            groupBoxGewichtLayout.addWidget(self.lineEditGewichtTestIdent, 0, 1)
            groupBoxGewichtLayout.addWidget(labelGewichtTestBezeichnung, 1, 0)
            groupBoxGewichtLayout.addWidget(self.lineEditGewichtTestBezeichnung, 1, 1)
            groupBoxGewichtLayout.addWidget(labelGewichtTestErgebnis, 2, 0)
            groupBoxGewichtLayout.addWidget(self.lineEditGewichtTestErgebnis, 2, 1)
            groupBoxGewichtLayout.addWidget(self.labelGewichtEinheitBerechnet, 2, 2)
            groupBoxGewichtLayout.addWidget(labelGewichtTestErgebnis, 2, 0)
            groupBoxGewichtLayout.addWidget(self.lineEditGewichtTestErgebnis, 2, 1)
            groupBoxGewichtLayout.addWidget(self.labelGewichtEinheitBerechnet, 2, 2)
            groupBoxGewichtLayout.addWidget(labelGewichtTestEinheit, 3, 0)
            groupBoxGewichtLayout.addWidget(self.comboBoxGewichtTestEinheit, 3, 1)
            groupBoxGewichtLayout.addWidget(self.checkBoxGewichtLoeschen, 4, 0, 1, 2)
            groupBoxGewicht.setLayout(groupBoxGewichtLayout)
            dialogLayoutH.addWidget(groupBoxGewicht)

        if self.groesseTest.getInhalt("8420") != "" and self.gewichtTest.getInhalt("8420") != "":
            bmifloat = self.gewichtFloat / self.groesseFloat / self.groesseFloat
            if self.gewichtFloat > 500:
                bmifloat /= 1000
            if self.groesseFloat > 3:
                bmifloat *= 10000
            groupBoxBmiLayout = QGridLayout()
            groupBoxBmi = QGroupBox("Body-Mass-Index (BMI)")
            groupBoxBmi.setFont(self.fontBold)
            labelBmiTestIdent = QLabel("Test-Ident")
            labelBmiTestIdent.setFont(self.fontNormal)
            self.lineEditBmiTestIdent = QLineEdit(self.bmiTest.getInhalt("8410"))
            self.lineEditBmiTestIdent.setFont(self.fontNormal)
            labelBmiTestBezeichnung = QLabel("Test-Bezeichnung")
            labelBmiTestBezeichnung.setFont(self.fontNormal)
            self.lineEditBmiTestBezeichnung = QLineEdit(self.bmiTest.getInhalt("8411"))
            self.lineEditBmiTestBezeichnung.setFont(self.fontNormal)
            labelBmiTestErgebnis = QLabel("Test-Ergebnis")
            labelBmiTestErgebnis.setFont(self.fontNormal)
            self.lineEditBmiTestErgebnis = QLineEdit("{:.1f}".format(bmifloat).replace(".", ","))
            self.lineEditBmiTestErgebnis.setFont(self.fontNormal)
            self.lineEditBmiTestErgebnis.setReadOnly(True)
            self.labelBmiEinheitBerechnet = QLabel("kg/m\u00b2")
            self.labelBmiEinheitBerechnet.setFont(self.fontNormal)
            labelBmiTestEinheit = QLabel("Test-Einheit*")
            labelBmiTestEinheit.setFont(self.fontNormal)
            self.lineEditBmiTestEinheit = QLineEdit(self.bmiTest.getInhalt("8421"))
            self.lineEditBmiTestEinheit.setFont(self.fontNormal)
            labelFussnote = QLabel("* Die BMI-Testeinheit kann geändert werden.\nDas Testergebnis hat unabhängig von dieser\nÄnderung die Einheit kg/m\u00b2.")
            labelFussnote.setFont(self.fontKlein)

            groupBoxBmiLayout.addWidget(labelBmiTestIdent, 0, 0)
            groupBoxBmiLayout.addWidget(self.lineEditBmiTestIdent, 0, 1)
            groupBoxBmiLayout.addWidget(labelBmiTestBezeichnung, 1, 0)
            groupBoxBmiLayout.addWidget(self.lineEditBmiTestBezeichnung, 1, 1)
            groupBoxBmiLayout.addWidget(labelBmiTestErgebnis, 2, 0)
            groupBoxBmiLayout.addWidget(self.lineEditBmiTestErgebnis, 2, 1)
            groupBoxBmiLayout.addWidget(self.labelBmiEinheitBerechnet, 2, 2)
            groupBoxBmiLayout.addWidget(labelBmiTestErgebnis, 2, 0)
            groupBoxBmiLayout.addWidget(self.lineEditBmiTestErgebnis, 2, 1)
            groupBoxBmiLayout.addWidget(self.labelBmiEinheitBerechnet, 2, 2)
            groupBoxBmiLayout.addWidget(labelBmiTestEinheit, 3, 0)
            groupBoxBmiLayout.addWidget(self.lineEditBmiTestEinheit, 3, 1)
            groupBoxBmiLayout.addWidget(labelFussnote, 4, 0, 1, 2)
            groupBoxBmi.setLayout(groupBoxBmiLayout)
            dialogLayoutH.addWidget(groupBoxBmi)

        dialogLayoutV.addLayout(dialogLayoutH)
        dialogLayoutV.addWidget(self.buttonBox)     

        self.setLayout(dialogLayoutV)

        # Test-Idents merken, falls Bearbeiten-Modus
        self.groesseTestIdentVergeben = ""
        if self.groesseVorhanden:
            self.groesseTestIdentVergeben = self.lineEditGroesseTestIdent.text()
        if self.gewichtVorhanden:
            self.gewichtTestIdentVergeben = self.lineEditGewichtTestIdent.text()
        if self.groesseVorhanden and self.gewichtVorhanden:
            self.bmiTestIdentVergeben = self.lineEditBmiTestIdent.text()
    
    def comboBoxGroesseTestEinheitChanged(self, text):
        if text == "m" and self.labelGroesseEinheitBerechnet.text() == "cm":
            self.groesseFloat /= 100
            self.lineEditGroesseTestErgebnis.setText("{:.2f}".format(self.groesseFloat).replace(".", ","))
            self.labelGroesseEinheitBerechnet.setText("m")
        elif text == "cm" and self.labelGroesseEinheitBerechnet.text() == "m":
            self.groesseFloat *= 100
            self.lineEditGroesseTestErgebnis.setText("{:.1f}".format(self.groesseFloat).replace(".", ",").replace(",0", ""))
            self.labelGroesseEinheitBerechnet.setText("cm")

    def comboBoxGewichtTestEinheitChanged(self, text):
        if text == "kg" and self.labelGewichtEinheitBerechnet.text() == "g":
            self.gewichtFloat /= 1000
            self.lineEditGewichtTestErgebnis.setText("{:.2f}".format(self.gewichtFloat).replace(".", ",").replace(",00", ""))
            self.labelGewichtEinheitBerechnet.setText("kg")
        elif text == "g" and self.labelGewichtEinheitBerechnet.text() == "kg":
            self.gewichtFloat *= 1000
            self.lineEditGewichtTestErgebnis.setText("{:.0f}".format(self.gewichtFloat))
            self.labelGewichtEinheitBerechnet.setText("g")

    def accept(self):
        groesseTestIdentUnveraendert = self.groesseTestIdentVergeben == self.lineEditGroesseTestIdent.text()
        gewichtTestIdentUnveraendert = self.gewichtVorhanden and self.gewichtTestIdentVergeben == self.lineEditGewichtTestIdent.text()
        bmiTestIdentUnveraendert = self.groesseVorhanden and self.gewichtVorhanden and self.bmiTestIdentVergeben == self.lineEditBmiTestIdent.text()
        self.checkBoxStatusGroesse = False
        self.checkBoxStatusGewicht = False
        fehler = []
        if self.groesseVorhanden:
            if self.lineEditGroesseTestIdent.text() == "":
                fehler.append("Kein Test-Ident für Größe eingetragen")
            else:
                alleTestIdents = self.gdtDateiOptimiert.getInhalte("8410")
                for i in range(len(alleTestIdents)):
                    if re.match(r"^.+__\d{4}__$", alleTestIdents[i]) != None:
                        alleTestIdents[i] = alleTestIdents[i][:-8]
                testIdentIsEindeutig = self.lineEditGroesseTestIdent.text() not in alleTestIdents or groesseTestIdentUnveraendert
                if not testIdentIsEindeutig:
                    fehler.append("Test-Ident für Größe ist nicht eindeutig.")
            if self.lineEditGroesseTestBezeichnung.text() == "":
                fehler.append("Keine Test-Bezeichnung für Größe eingetragen")

        if self.gewichtVorhanden:
            if self.lineEditGewichtTestIdent.text() == "":
                fehler.append("Kein Test-Ident für Gewicht eingetragen")
            elif self.lineEditGewichtTestIdent.text() == self.lineEditGroesseTestIdent.text():
                fehler.append("Test-Ident für Gewicht ist nicht eindeutig.")
            else:
                alleTestIdents = self.gdtDateiOptimiert.getInhalte("8410")
                for i in range(len(alleTestIdents)):
                    if re.match(r"^.+__\d{4}__$", alleTestIdents[i]) != None:
                        alleTestIdents[i] = alleTestIdents[i][:-8]
                testIdentIsEindeutig = self.lineEditGewichtTestIdent.text() not in alleTestIdents or gewichtTestIdentUnveraendert
                if not testIdentIsEindeutig:
                    fehler.append("Test-Ident für Gewicht ist nicht eindeutig.")
            if self.lineEditGewichtTestBezeichnung.text() == "":
                fehler.append("Keine Test-Bezeichnung für Gewicht eingetragen")

        if self.groesseVorhanden and self.gewichtVorhanden:
            if self.lineEditBmiTestIdent.text() == "":
                fehler.append("Kein Test-Ident für BMI eingetragen")
            elif self.lineEditBmiTestIdent.text() == self.lineEditGroesseTestIdent.text() or self.lineEditBmiTestIdent.text() == self.lineEditGewichtTestIdent.text():
                fehler.append("Test-Ident für BMI ist nicht eindeutig.")
            else:
                alleTestIdents = self.gdtDateiOptimiert.getInhalte("8410")
                for i in range(len(alleTestIdents)):
                    if re.match(r"^.+__\d{4}__$", alleTestIdents[i]) != None:
                        alleTestIdents[i] = alleTestIdents[i][:-8]
                testIdentIsEindeutig = self.lineEditBmiTestIdent.text() not in alleTestIdents or bmiTestIdentUnveraendert
                if not testIdentIsEindeutig:
                    fehler.append("Test-Ident für BMI ist nicht eindeutig.")
            if self.lineEditBmiTestBezeichnung.text() == "":
                fehler.append("Keine Test-Bezeichnung für BMI eingetragen")
        
        if len(fehler) == 0:  
            if self.groesseVorhanden:
                self.groesseTest.setZeile("8410", self.lineEditGroesseTestIdent.text())
                self.groesseTest.setZeile("8411", self.lineEditGroesseTestBezeichnung.text())
                self.groesseTest.setZeile("8421", self.comboBoxGroesseTestEinheit.currentText())
                self.checkBoxStatusGroesse = self.checkBoxGroesseLoeschen.isChecked()
            if self.gewichtVorhanden:
                self.gewichtTest.setZeile("8410", self.lineEditGewichtTestIdent.text())
                self.gewichtTest.setZeile("8411", self.lineEditGewichtTestBezeichnung.text())
                self.gewichtTest.setZeile("8421", self.comboBoxGewichtTestEinheit.currentText())
                self.checkBoxStatusGewicht = self.checkBoxGewichtLoeschen.isChecked()
            if self.groesseVorhanden and self.gewichtVorhanden:
                self.bmiTest.setZeile("8410", self.lineEditBmiTestIdent.text())
                self.bmiTest.setZeile("8411", self.lineEditBmiTestBezeichnung.text())
                self.bmiTest.setZeile("8421", self.lineEditBmiTestEinheit.text())
            self.done(1)
        else:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Formular nicht korrekt ausgefüllt:\n- " + "\n- ".join(fehler), QMessageBox.StandardButton.Ok)
            mb.exec()