import configparser, os, re
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFileDialog,
    QComboBox
)

zeichensatz = ["7Bit", "IBM (Standard) CP 437", "ISO8859-1 (ANSI) CP 1252"]
reZahlPattern = r"^\d+$"
class EinstellungenOptimierung(QDialog):
    def __init__(self, configPath):
        super().__init__()
        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontNormal.setItalic(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)

        #config.ini lesen
        configIni = configparser.ConfigParser()
        configIni.read(os.path.join(configPath, "config.ini"))
        self.standardTemplateverzeichnis = configIni["Optimierung"]["standardtemplateverzeichnis"]
        self.maxEindeutigkeitskriterien = configIni["Optimierung"]["maxeindeutigkeitskriterien"]
        self.maxTeständerungen = configIni["Optimierung"]["maxtestaenderungen"]
        self.maxAnzahl6228Spalten = configIni["Optimierung"]["maxanzahl6228spalten"]
        self.standard6228TrennRegexPattern = configIni["Optimierung"]["standard6228trennregexpattern"]
        self.sekundenBisTemplatebearbeitung = configIni["Optimierung"]["sekundenbistemplatebearbeitung"]
        self.punktinkomma6220 = configIni["Optimierung"]["punktinkomma6220"] == "True"

        self.setWindowTitle("Optimierungs-Einstellungen")
        self.setMinimumWidth(500)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type:ignore
        self.buttonBox.rejected.connect(self.reject) # type:ignore

        dialogLayoutV = QVBoxLayout()
        # Groupbox Template
        groupboxTemplateLayout = QGridLayout()
        groupboxTemplate = QGroupBox("Templates")
        groupboxTemplate.setFont(self.fontBold)
        groupboxTemplate.setLayout(groupboxTemplateLayout)
        labelTemplateverzeichnis = QLabel("Standard-Verzeichnis")
        labelTemplateverzeichnis.setFont(self.fontNormal)
        self.lineEditTemplateverzeichnis = QLineEdit(self.standardTemplateverzeichnis)
        self.lineEditTemplateverzeichnis.setStyleSheet("font-weight:normal")
        self.lineEditTemplateverzeichnis.setReadOnly(True)
        labelVerzoegerung = QLabel("Verzögerung bis zur Bearbeitung [Sekunden]")
        labelVerzoegerung.setFont(self.fontNormal)
        self.lineEditVerzoegerung = QLineEdit(self.sekundenBisTemplatebearbeitung)
        self.lineEditVerzoegerung.setFont(self.fontNormal)
        self.pushButtonDurchsuchenTemplateverzeichnis = QPushButton("...")
        self.pushButtonDurchsuchenTemplateverzeichnis.setStyleSheet("font-weight:normal")
        self.pushButtonDurchsuchenTemplateverzeichnis.setToolTip("Durchsuchen")
        self.pushButtonDurchsuchenTemplateverzeichnis.clicked.connect(self.pushBbuttonDurchsuchenTemplateverzeichnisClicked) # type:ignore
        groupboxTemplateLayout.addWidget(labelTemplateverzeichnis, 0, 0)
        groupboxTemplateLayout.addWidget(self.lineEditTemplateverzeichnis, 1, 0)
        groupboxTemplateLayout.addWidget(self.pushButtonDurchsuchenTemplateverzeichnis, 1, 1)
        groupboxTemplateLayout.addWidget(labelVerzoegerung, 2, 0)
        groupboxTemplateLayout.addWidget(self.lineEditVerzoegerung, 3, 0)
        
        # Groupbox Test ändern/entfernen, Befund aus Test
        groupboxTestLayout = QVBoxLayout()
        groupboxTest = QGroupBox("Test ändern/entfernen, Befund aus Test")
        groupboxTest.setFont(self.fontBold)
        groupboxTest.setLayout(groupboxTestLayout)
        labelMaxEindeutigkeitskriterien = QLabel("Maximale Anzahl Eindeutigkeitskriterien")
        labelMaxEindeutigkeitskriterien.setFont(self.fontNormal)
        self.lineEditMaxEindutigkeitskriterien = QLineEdit(self.maxEindeutigkeitskriterien)
        self.lineEditMaxEindutigkeitskriterien.setFont(self.fontNormal)
        labelMaxAenderungenProTest = QLabel("Maximale Anzahl Änderungen pro Test")
        labelMaxAenderungenProTest.setFont(self.fontNormal)
        self.lineEditMaxAenderungenProTest = QLineEdit(self.maxTeständerungen)
        self.lineEditMaxAenderungenProTest.setFont(self.fontNormal)
        groupboxTestLayout.addWidget(labelMaxEindeutigkeitskriterien)
        groupboxTestLayout.addWidget(self.lineEditMaxEindutigkeitskriterien)
        groupboxTestLayout.addWidget(labelMaxAenderungenProTest)
        groupboxTestLayout.addWidget(self.lineEditMaxAenderungenProTest)
        
        # Groupbox Test aus 6228-Zeile
        groupboxTestAus6228Layout = QVBoxLayout()
        groupboxTestAus6228 = QGroupBox("Test aus 6228-Zeile")
        groupboxTestAus6228.setFont(self.fontBold)
        groupboxTestAus6228.setLayout(groupboxTestAus6228Layout)
        labelMaxAnzahl6228Spalten = QLabel("Maximale Anzahl 6228-Spalten")
        labelMaxAnzahl6228Spalten.setFont(self.fontNormal)
        self.lineEditMaxAnzahl6228Spalten = QLineEdit(self.maxAnzahl6228Spalten)
        self.lineEditMaxAnzahl6228Spalten.setFont(self.fontNormal)
        labelStandardTrennzeichen = QLabel("Standard-Spaltentrennzeichen/regulärer Ausdruck")
        labelStandardTrennzeichen.setFont(self.fontNormal)
        self.lineEditStandardSpaltenTrennzeichen = QLineEdit(self.standard6228TrennRegexPattern)
        self.lineEditStandardSpaltenTrennzeichen.setFont(self.fontNormal)
        groupboxTestAus6228Layout.addWidget(labelMaxAnzahl6228Spalten)
        groupboxTestAus6228Layout.addWidget(self.lineEditMaxAnzahl6228Spalten)
        groupboxTestAus6228Layout.addWidget(labelStandardTrennzeichen)
        groupboxTestAus6228Layout.addWidget(self.lineEditStandardSpaltenTrennzeichen)

        # GroupboxAllgemein
        groupboxAllgemeinLayout = QGridLayout()
        groupboxAllgemein = QGroupBox("Allgemein")
        groupboxAllgemein.setFont(self.fontBold)
        self.checkboxPunktInKomma = QCheckBox("Dezimalkomma statt -punkt in Befund (6220)")
        self.checkboxPunktInKomma.setFont(self.fontNormal)
        self.checkboxPunktInKomma.setChecked(self.punktinkomma6220)
        groupboxAllgemeinLayout.addWidget(self.checkboxPunktInKomma, 0, 0)
        groupboxAllgemein.setLayout(groupboxAllgemeinLayout)

        dialogLayoutV.addWidget(groupboxTemplate)
        dialogLayoutV.addWidget(groupboxTest)
        dialogLayoutV.addWidget(groupboxTestAus6228)
        dialogLayoutV.addWidget(groupboxAllgemein)
        dialogLayoutV.addWidget(self.buttonBox)
        self.setLayout(dialogLayoutV)

    def pushBbuttonDurchsuchenTemplateverzeichnisClicked(self):
        fd = QFileDialog(self)
        fd.setFileMode(QFileDialog.FileMode.Directory)
        fd.setWindowTitle("Templateverzeichnis")
        fd.setDirectory(self.standardTemplateverzeichnis)
        fd.setModal(True)
        fd.setLabelText(QFileDialog.DialogLabel.Accept, "Ok")
        fd.setLabelText(QFileDialog.DialogLabel.Reject, "Abbrechen")
        if fd.exec() == 1:
            self.standardTemplateverzeichnis = fd.directory()
            self.lineEditTemplateverzeichnis.setText(fd.directory().path())

    def accept(self):
        formularOk = True
        if re.match(reZahlPattern, self.lineEditVerzoegerung.text()) == None:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Die Verzögerungangabe muss eine Zahl sein.", QMessageBox.StandardButton.Ok)
            mb.exec()
            self.lineEditVerzoegerung.setFocus()
            self.lineEditVerzoegerung.selectAll()
            formularOk = False
        if formularOk:
            self.done(1)
