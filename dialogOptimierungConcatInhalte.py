import re
import class_Enums, class_gdtdatei
from PySide6.QtGui import QFont, Qt
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QGroupBox,
    QLineEdit,
    QMessageBox,
    QLabel,
    QComboBox,
    QCheckBox
)

reFeldkennung = r"^\d{4}$"

class OptimierungConcatInhalte(QDialog):
    def __init__(self, gdtDateiOriginal:class_gdtdatei.GdtDatei, feldkennung:str, feldkennungAnfang:str, inhaltAnfang:str, inkludiertAnfang:bool, feldkennungEnde:str, inhaltEnde:str, inkludiertEnde:bool, feldkennungZu:str, leerzeichenAnfangEntfernen:bool, leerzeichenEndeEntfernen:bool, einzufuegendesZeichen:class_Enums.EinzufuegendeZeichen):
        super().__init__()
        self.gdtDateiOriginal = gdtDateiOriginal
        self.feldkennung = feldkennung
        self.feldkennungAnfang = feldkennungAnfang
        self.inhaltAnfang = inhaltAnfang
        self.inkludiertAnfang = inkludiertAnfang
        self.feldkennungEnde = feldkennungEnde
        self.inhaltEnde = inhaltEnde
        self.inkludiertEnde = inkludiertEnde
        self.feldkennungZu = feldkennungZu
        self.leerzeichenAnfangEntfernen = leerzeichenAnfangEntfernen
        self.leerzeichenEndeEntfernen = leerzeichenEndeEntfernen
        self.einzufuegendesZeichen = einzufuegendesZeichen
        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)

        self.setWindowTitle("GDT-Optimierung: Inhalte zusammenführen")
        self.setMinimumWidth(300)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type:ignore
        self.buttonBox.rejected.connect(self.reject) # type:ignore

        dialogLayoutV = QVBoxLayout()
        dialogLayoutG = QGridLayout()
        labelFeldkennung = QLabel("Zusammenführen aus Feldkennung")
        labelFeldkennung.setFont(self.fontNormal)
        self.lineEditFeldkennung = QLineEdit(self.feldkennung)
        if self.feldkennungAnfang != "" and self.feldkennung != self.feldkennungAnfang:
            self.lineEditFeldkennung.setText(self.feldkennungAnfang) # Bearbeiten
        self.lineEditFeldkennung.setFont(self.fontNormal)
        self.lineEditFeldkennung.setPlaceholderText("z. B. 6220")
        self.lineEditFeldkennung.textEdited.connect(self.lineEditFeldkennungChanged)

        groupBoxBegrenzung = QGroupBox("Begrenzungen")
        groupBoxBegrenzung.setFont(self.fontBold)
        begrenzungLayoutG = QGridLayout()
        labelBegrenzungFeldkennung = QLabel("Feldkennung")
        labelBegrenzungFeldkennung.setFont(self.fontNormal)
        labelBegrenzungInhalt = QLabel("Inhalt (Regulärer Ausdruck)")
        labelBegrenzungInhalt.setFont(self.fontNormal)
        labelBegrenzungInkludiert = QLabel("Inkludiert")
        labelBegrenzungInkludiert.setFont(self.fontNormal)
        labelBegrenzungAnfang = QLabel("Begrenzung Anfang")
        labelBegrenzungAnfang.setFont(self.fontNormal)
        self.lineEditFeldkennungAnfang = QLineEdit(self.feldkennungAnfang)
        self.lineEditFeldkennungAnfang.setFont(self.fontNormal)
        self.lineEditInhaltAnfang = QLineEdit(self.inhaltAnfang)
        self.lineEditInhaltAnfang.setFont(self.fontNormal)
        self.checkBoxInkludiertAnfang = QCheckBox()
        self.checkBoxInkludiertAnfang.setChecked(self.inkludiertAnfang)
        labelBegrenzungEnde = QLabel("Begrenzung Ende")
        labelBegrenzungEnde.setFont(self.fontNormal)
        self.lineEditFeldkennungEnde = QLineEdit(self.feldkennungEnde)
        self.lineEditFeldkennungEnde.setFont(self.fontNormal)
        self.lineEditInhaltEnde = QLineEdit(self.inhaltEnde)
        self.lineEditInhaltEnde.setFont(self.fontNormal)
        self.checkBoxInkludiertEnde = QCheckBox()
        self.checkBoxInkludiertEnde.setChecked(self.inkludiertEnde)
        begrenzungLayoutG.addWidget(labelBegrenzungFeldkennung, 0, 1, 1, 1)
        begrenzungLayoutG.addWidget(labelBegrenzungInhalt, 0, 2, 1, 1)
        begrenzungLayoutG.addWidget(labelBegrenzungInkludiert, 0, 3, 1, 1)
        begrenzungLayoutG.addWidget(labelBegrenzungAnfang, 1, 0, 1, 1)
        begrenzungLayoutG.addWidget(self.lineEditFeldkennungAnfang, 1, 1, 1, 1)
        begrenzungLayoutG.addWidget(self.lineEditInhaltAnfang, 1, 2, 1, 1)
        begrenzungLayoutG.addWidget(self.checkBoxInkludiertAnfang, 1, 3, 1, 1, Qt.AlignmentFlag.AlignCenter)
        begrenzungLayoutG.addWidget(labelBegrenzungEnde, 2, 0, 1, 1)
        begrenzungLayoutG.addWidget(self.lineEditFeldkennungEnde, 2, 1, 1, 1)
        begrenzungLayoutG.addWidget(self.lineEditInhaltEnde, 2, 2, 1, 1)
        begrenzungLayoutG.addWidget(self.checkBoxInkludiertEnde, 2, 3, 1, 1, Qt.AlignmentFlag.AlignCenter)
        groupBoxBegrenzung.setLayout(begrenzungLayoutG)
        labelFeldkennungZu = QLabel("Zusammenführen in Feldkennung")
        labelFeldkennungZu.setFont(self.fontNormal)
        self.lineEditFeldkennungZu = QLineEdit(self.feldkennungZu)
        self.lineEditFeldkennungZu.setFont(self.fontNormal)
        self.lineEditFeldkennungZu.setPlaceholderText(self.lineEditFeldkennung.text())
        labelLeerzeichenAnfangEntfernen = QLabel("Leerzeichen am Anfang einer Zeile entfernen")
        labelLeerzeichenAnfangEntfernen.setFont(self.fontNormal)
        self.checkBoxLeerzeichenAnfangEntfernen = QCheckBox()
        self.checkBoxLeerzeichenAnfangEntfernen.setChecked(self.leerzeichenAnfangEntfernen)
        labelLeerzeichenEndeEntfernen = QLabel("Leerzeichen am Ende einer Zeile entfernen")
        labelLeerzeichenEndeEntfernen.setFont(self.fontNormal)
        self.checkBoxLeerzeichenEndeEntfernen = QCheckBox()
        self.checkBoxLeerzeichenEndeEntfernen.setChecked(self.leerzeichenEndeEntfernen)
        labelZeichenEinfuegen = QLabel("Zeichen zwischen den zusammengefügten Zeilen einfügen")
        labelZeichenEinfuegen.setFont(self.fontNormal)
        self.comboBoxZeichenEinfuegen = QComboBox()
        self.comboBoxZeichenEinfuegen.setFont(self.fontNormal)
        einzufuegendeZeichen = []
        for ez in class_Enums.EinzufuegendeZeichen:
            einzufuegendeZeichen.append(ez.name.replace("_", " "))
        self.comboBoxZeichenEinfuegen.addItems(einzufuegendeZeichen)
        if einzufuegendesZeichen in class_Enums.EinzufuegendeZeichen:
            self.comboBoxZeichenEinfuegen.setCurrentText(einzufuegendesZeichen.name.replace("_", " "))
        else:
            self.comboBoxZeichenEinfuegen.setCurrentIndex(0)
        dialogLayoutG.addWidget(labelFeldkennung, 0, 0)
        dialogLayoutG.addWidget(self.lineEditFeldkennung, 0, 1)
        dialogLayoutG.addWidget(groupBoxBegrenzung, 1, 0, 1, 2)
        dialogLayoutG.addWidget(labelFeldkennungZu, 2, 0)
        dialogLayoutG.addWidget(self.lineEditFeldkennungZu, 2, 1)
        dialogLayoutG.addWidget(labelLeerzeichenAnfangEntfernen, 3, 0)
        dialogLayoutG.addWidget(self.checkBoxLeerzeichenAnfangEntfernen, 3, 1)
        dialogLayoutG.addWidget(labelLeerzeichenEndeEntfernen, 4, 0)
        dialogLayoutG.addWidget(self.checkBoxLeerzeichenEndeEntfernen, 4, 1)
        dialogLayoutG.addWidget(labelZeichenEinfuegen, 5, 0)
        dialogLayoutG.addWidget(self.comboBoxZeichenEinfuegen, 5, 1)
        dialogLayoutV.addLayout(dialogLayoutG)
        dialogLayoutV.addWidget(self.buttonBox)

        self.setLayout(dialogLayoutV)
        self.lineEditFeldkennung.setFocus()
        self.lineEditFeldkennung.selectAll()

    def lineEditFeldkennungChanged(self):
        self.lineEditFeldkennungZu.setPlaceholderText(self.lineEditFeldkennung.text())

    def accept(self):
        if not re.match(reFeldkennung, self.lineEditFeldkennung.text()):
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Die Feldkennung muss aus vier Ziffern bestehen.", QMessageBox.StandardButton.Ok)
            mb.exec()
            self.lineEditFeldkennung.setFocus()
            self.lineEditFeldkennung.selectAll()
        elif self.lineEditFeldkennungZu.text() != "" and not re.match(reFeldkennung, self.lineEditFeldkennungZu.text()):
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Die Feldkennung muss aus vier Ziffern bestehen.", QMessageBox.StandardButton.Ok)
            mb.exec()
            self.lineEditFeldkennungZu.setFocus()
            self.lineEditFeldkennungZu.selectAll()
        elif self.lineEditFeldkennungAnfang.text() != "" and not re.match(reFeldkennung, self.lineEditFeldkennungAnfang.text()):
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Die Feldkennung muss aus vier Ziffern bestehen.", QMessageBox.StandardButton.Ok)
            mb.exec()
            self.lineEditFeldkennungAnfang.setFocus()
            self.lineEditFeldkennungAnfang.selectAll()
        elif self.lineEditFeldkennungAnfang.text() != "" and self.lineEditInhaltAnfang.text() == "":
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Kein Inhalt für die Anfangsbegrenzung angegeben.", QMessageBox.StandardButton.Ok)
            mb.exec()
            self.lineEditInhaltAnfang.setFocus()
            self.lineEditInhaltAnfang.selectAll()
        elif self.lineEditFeldkennungEnde.text() != "" and not re.match(reFeldkennung, self.lineEditFeldkennungEnde.text()):
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Die Feldkennung muss aus vier Ziffern bestehen.", QMessageBox.StandardButton.Ok)
            mb.exec()
            self.lineEditFeldkennungEnde.setFocus()
            self.lineEditFeldkennungEnde.selectAll()
        elif self.lineEditFeldkennungEnde.text() != "" and self.lineEditInhaltEnde.text() == "":
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Kein Inhalt für die Anfangsbegrenzung angegeben.", QMessageBox.StandardButton.Ok)
            mb.exec()
            self.lineEditInhaltEnde.setFocus()
            self.lineEditInhaltEnde.selectAll()
        elif not self.gdtDateiOriginal.feldkennungVorhanden(self.lineEditFeldkennung.text()):
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Die Feldkennung " + self.lineEditFeldkennung.text() + " ist in der Original-GDT-Datei nicht vorhanden.", QMessageBox.StandardButton.Ok)
            mb.exec()
            self.lineEditFeldkennung.setFocus()
            self.lineEditFeldkennung.selectAll()
        else:
            if self.lineEditFeldkennungZu.text() == "":
                self.lineEditFeldkennungZu.setText(self.lineEditFeldkennung.text())
            # Auf Eindeutigkeit prüfen
            haeufigkeitInhaltAnfang = 0
            haeufigkeitInhaltEnde = 0
            for zeile in self.gdtDateiOriginal.getZeilen():
                tempFeldkennung = zeile[3:7]
                tempInhalt = zeile[7:]
                if tempFeldkennung == self.lineEditFeldkennungAnfang.text() and re.search(self.lineEditInhaltAnfang.text(), tempInhalt) != None:
                    haeufigkeitInhaltAnfang += 1
                if tempFeldkennung == self.lineEditFeldkennungEnde.text() and re.search(self.lineEditInhaltEnde.text(), tempInhalt) != None:
                    haeufigkeitInhaltEnde += 1
            inhaltAnfangEindeutig = haeufigkeitInhaltAnfang == 1
            inhaltEndeEindeutig = haeufigkeitInhaltEnde == 1
            if not inhaltAnfangEindeutig:
                meldung = "Der Inhalt der Anfangbegrenzung \"" + self.lineEditInhaltAnfang.text() + "\" ist innerhalb der GDT-Datei nicht eindeutig."
                if haeufigkeitInhaltAnfang == 0:
                    meldung = "Der Inhalt der Anfangbegrenzung \"" + self.lineEditInhaltAnfang.text() + "\" kommt innerhalb der GDT-Datei nicht vor."
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", meldung, QMessageBox.StandardButton.Ok)
                mb.exec()
                self.lineEditInhaltAnfang.setFocus()
                self.lineEditInhaltAnfang.selectAll()
            elif not inhaltEndeEindeutig:
                meldung = "Der Inhalt der Endebegrenzung \"" + self.lineEditInhaltEnde.text() + "\" ist innerhalb der GDT-Datei nicht eindeutig."
                if haeufigkeitInhaltEnde == 0:
                    meldung = "Der Inhalt der Endebegrenzung \"" + self.lineEditInhaltEnde.text() + "\" kommt innerhalb der GDT-Datei nicht vor."
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", meldung, QMessageBox.StandardButton.Ok)
                mb.exec()
                self.lineEditInhaltEnde.setFocus()
                self.lineEditInhaltEnde.selectAll()
            else:    
                self.done(1)