import re, os, sys, logger
import xml.etree.ElementTree as ElementTree
from PySide6.QtGui import Qt, QFont, QAction
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFileDialog,
    QCheckBox
)

reKennfeld = r"^[A-Z]{1,4}[0-9]{2}$"
reGdtId = r"^[0-9A-Za-z_\-]{8}$"
reGdtDateiendung = r"^\.gdt|\.\d{3}$"

if sys.platform == "win32":
    updateSafePath = os.path.expanduser("~\\appdata\\local\\optigdt")
else:
    updateSafePath = os.path.expanduser("~/.config/optigdt")

class TemplatesVerwalten(QDialog):
    def __init__(self, templateverzeichnis:str):
        super().__init__()
        self.templateverzeichnis = templateverzeichnis
        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontNormal.setItalic(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)
        self.fontBoldItalic = QFont()
        self.fontBoldItalic.setBold(True)
        self.fontBoldItalic.setItalic(True)

        self.setWindowTitle("Templates verwalten")
        self.setMinimumWidth(800)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type: ignore
        self.buttonBox.rejected.connect(self.reject) # type: ignore

        # Templates finden
        files = os.listdir(self.templateverzeichnis)
        self.templatenamen = []
        for filename in files:
            if len(filename) > 4:
                dateiendung = filename[-4:]
                if dateiendung == ".ogt":
                    self.templatenamen.append(filename)

        # Formular aufbauen
        dialogLayoutV = QVBoxLayout()
        dialogLayoutG = QGridLayout()
        groupBoxGeräte = QGroupBox("Templates im Verzeichnis \"" + templateverzeichnis + "\"")
        groupBoxGeräte.setFont(self.fontBold)
        groupBoxGeräte.setLayout(dialogLayoutG)
        labelLoeschen = QLabel("\U0001f5d1")
        labelLoeschen.setFont(self.fontNormal)
        labelName = QLabel("Name")
        labelName.setFont(self.fontNormal)
        labelKennfeld = QLabel("Gerätespez. Kennfeld")
        labelKennfeld.setFont(self.fontNormal)
        labelKennfeld.setToolTip("Gerätespezifisches Kennfeld")
        labelGdtId = QLabel("GDT-ID")
        labelGdtId.setFont(self.fontNormal)
        labelGdtDateiname = QLabel("GDT-Dateiname\u00b9")
        labelGdtDateiname.setFont(self.fontNormal)
        labelExportverzeichnis = QLabel("Exportverzeichnis\u00b2")
        labelExportverzeichnis.setFont(self.fontNormal)
        dialogLayoutG.addWidget(labelLoeschen, 0, 0)
        dialogLayoutG.addWidget(labelName, 0, 1)
        dialogLayoutG.addWidget(labelKennfeld, 0, 2)
        dialogLayoutG.addWidget(labelGdtId, 0, 3)
        dialogLayoutG.addWidget(labelGdtDateiname, 0, 4)
        dialogLayoutG.addWidget(labelExportverzeichnis, 0, 5)
        self.checkBoxLoeschen = []
        self.lineEditName = []
        self.lineEditKennfeld = []
        self.lineEditGdtId = []
        self.lineEditGdtDateiname = []
        self.lineEditExportverzeichnis = []
        self.pushButtonDurchsuchen = []

        for i in range(len(self.templatenamen)):
            self.checkBoxLoeschen.append(QCheckBox())
            self.checkBoxLoeschen[i].setToolTip("Template löschen")
            self.lineEditName.append(QLineEdit())
            self.lineEditName[i].setFont(self.fontNormal)
            self.lineEditKennfeld.append(QLineEdit())
            self.lineEditKennfeld[i].setFont(self.fontNormal)
            self.lineEditGdtId.append(QLineEdit())
            self.lineEditGdtId[i].setFont(self.fontNormal)
            self.lineEditGdtDateiname.append(QLineEdit())
            self.lineEditGdtDateiname[i].setFont(self.fontNormal)
            self.lineEditExportverzeichnis.append(QLineEdit())
            self.lineEditExportverzeichnis[i].setFont(self.fontNormal)
            self.lineEditExportverzeichnis[i].setReadOnly(True)
            self.pushButtonDurchsuchen.append(QPushButton("..."))
            self.pushButtonDurchsuchen[i].setFont(self.fontNormal)
            self.pushButtonDurchsuchen[i].clicked.connect(lambda checked = False, templatenummer = i:self.pushButtonDurchsuchenClicked(checked, templatenummer)) # type: ignore
            dialogLayoutG.addWidget(self.checkBoxLoeschen[i], (i + 1), 0)
            dialogLayoutG.addWidget(self.lineEditName[i], (i + 1), 1)
            dialogLayoutG.addWidget(self.lineEditKennfeld[i], (i + 1), 2)
            dialogLayoutG.addWidget(self.lineEditGdtId[i], (i + 1), 3)
            dialogLayoutG.addWidget(self.lineEditGdtDateiname[i], (i + 1), 4)
            dialogLayoutG.addWidget(self.lineEditExportverzeichnis[i], (i + 1), 5)
            dialogLayoutG.addWidget(self.pushButtonDurchsuchen[i], (i + 1), 6)
        labelFussnote1 = QLabel("\u00b9 Muss auf \".gdt\" oder \".000\" - \".999\" enden")
        labelFussnote1.setFont(self.fontNormal)
        labelFussnote2 = QLabel("\u00b2 Verzeichnis, aus dem das Praxisverwaltungssystem (PVS) die Datei importiert (GDT-Importverzeichnis des PVS)")
        labelFussnote2.setFont(self.fontNormal)
        self.pushButtonReferenzverzeichnisBereinigen = QPushButton("Referenz-GDT-Dateiverzeichnis bereinigen")
        self.pushButtonReferenzverzeichnisBereinigen.setFont(self.fontNormal)
        self.pushButtonReferenzverzeichnisBereinigen.clicked.connect(self.pushButtonReferenzverzeichnisBereinigenClicked)
        
        dialogLayoutV.addWidget(groupBoxGeräte)
        dialogLayoutV.addWidget(labelFussnote1)
        dialogLayoutV.addWidget(labelFussnote2)
        dialogLayoutV.addWidget(self.pushButtonReferenzverzeichnisBereinigen)
        dialogLayoutV.addWidget(self.buttonBox)
        self.setLayout(dialogLayoutV)

        self.FormularFuellen()

    def FormularFuellen(self):
        i = 0
        for name in self.templatenamen:
            tree = ElementTree.parse(os.path.join(self.templateverzeichnis, name))
            rootElement = tree.getroot()
            kennfeld = str(rootElement.get("kennfeld"))
            kennfeldPr = kennfeld != ""
            gdtId = str(rootElement.get("gdtIdGeraet"))
            gdtIdPr = gdtId != ""
            gdtDateiname = str(rootElement.get("gdtDateiname")) 
            gdtDateinamePr = gdtDateiname != ""
            exportverzeichnis = str(rootElement.get("exportverzeichnis"))
            self.lineEditName[i].setText(name[:-4])
            self.lineEditKennfeld[i].setText(kennfeld)
            self.lineEditGdtId[i].setText(gdtId)
            self.lineEditGdtDateiname[i].setText(gdtDateiname)
            self.lineEditExportverzeichnis[i].setText(exportverzeichnis)
            self.lineEditExportverzeichnis[i].setToolTip(exportverzeichnis)
            i += 1

    def pushButtonDurchsuchenClicked(self, checked, templatenummer):
        fd = QFileDialog(self)
        fd.setFileMode(QFileDialog.FileMode.Directory)
        fd.setWindowTitle("Exportverzeichnis")
        if os.path.exists(self.lineEditExportverzeichnis[templatenummer].text()):
            fd.setDirectory(self.lineEditExportverzeichnis[templatenummer].text())
        fd.setModal(True)
        fd.setLabelText(QFileDialog.DialogLabel.Accept, "Ok")
        fd.setLabelText(QFileDialog.DialogLabel.Reject, "Abbrechen")
        if fd.exec() == 1:
            self.lineEditExportverzeichnis[templatenummer].setText(os.path.abspath(fd.directory().path()))
            self.lineEditExportverzeichnis[templatenummer].setToolTip(os.path.abspath(fd.directory().path()))

    def pushButtonReferenzverzeichnisBereinigenClicked(self):
        referenzGdtDateiverzeichnis = os.path.join(updateSafePath, "gdtreferenzen")
        bereinigungsliste = []
        for referenzGdtDatei in os.listdir(referenzGdtDateiverzeichnis):
            templateVorhanden = False
            for templateDatei in os.listdir(self.templateverzeichnis):
                if templateDatei[:-4] in referenzGdtDatei:
                    templateVorhanden = True
                    break
            if not templateVorhanden:
                bereinigungsliste.append(referenzGdtDatei)
        if len(bereinigungsliste) > 0:
            bereinigungslisteFormatiert = str.join("\n- ", bereinigungsliste)
            sinPlu1 = "folgenden Referenz-GDT-Dateien"
            sinPlu2 = "Sollen"
            if len(bereinigungsliste) == 1:
                sinPlu1 = "folgende Referenz-GDT-Datei"
                sinPlu2 = "Soll"
            mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Für die " + sinPlu1 + " existiert kein Template:\n- " + bereinigungslisteFormatiert + "\n"  + sinPlu2 + " diese entfernt werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            mb.setDefaultButton(QMessageBox.StandardButton.No)
            mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
            mb.button(QMessageBox.StandardButton.No).setText("Nein")
            if mb.exec() == QMessageBox.StandardButton.Yes:
                for datei in bereinigungsliste:
                    try:
                        os.unlink(os.path.join(referenzGdtDateiverzeichnis, datei))
                    except:
                        mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Problem beim Entfernen der Datei " + datei + ".", QMessageBox.StandardButton.Ok)
                        mb.exec()
        else: 
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Das Referenz-GDT-Dateiverzeichnis ist bereits bereinigt.", QMessageBox.StandardButton.Ok)
            mb.exec()
    
    def accept(self):
        formularOk = True
        for i in range(len(self.templatenamen)):
            if self.lineEditName[i].text().strip() != "":
                if self.lineEditKennfeld[i].text().strip() != "" and re.match(reKennfeld, self.lineEditKennfeld[i].text().strip()) == None:
                    mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Das gerätespezifische Kennfeld für das Template \"" + self.lineEditName[i].text() + "\" sollte aus bis zu vier Buchstaben, gefolgt von zwei Ziffern bestehen.\nSoll es dennoch so übernommen werden (" + self.lineEditKennfeld[i].text().strip() + ")?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    mb.setDefaultButton(QMessageBox.StandardButton.No)
                    mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                    mb.button(QMessageBox.StandardButton.No).setText("Nein")
                    if mb.exec() == QMessageBox.StandardButton.No:
                        self.lineEditKennfeld[i].setFocus()
                        self.lineEditKennfeld[i].selectAll()
                        formularOk = False
                        break
                if self.lineEditGdtId[i].text().strip() != "" and re.match(reGdtId, self.lineEditGdtId[i].text().strip()) == None:
                    mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Die GDT-ID für das Template \"" + self.lineEditName[i].text() + "\" sollte aus acht Zeichen bestehen.\nSoll sie dennoch so übernommen werden (" + self.lineEditGdtId[i].text().strip() + ")?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    mb.setDefaultButton(QMessageBox.StandardButton.No)
                    mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                    mb.button(QMessageBox.StandardButton.No).setText("Nein")
                    if mb.exec() == QMessageBox.StandardButton.No:
                        self.lineEditGdtId[i].setFocus()
                        self.lineEditGdtId[i].selectAll()
                        formularOk = False
                        break
                if self.lineEditGdtDateiname[i].text().strip() == "" or re.match(reGdtDateiendung, self.lineEditGdtDateiname[i].text().strip()[-4:].lower()) == None:
                    mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Der GDT-Dateiname für das Template \"" + self.lineEditName[i].text().strip() + "\" ist unzulässig.", QMessageBox.StandardButton.Ok)
                    mb.exec()
                    self.lineEditGdtDateiname[i].setFocus()
                    self.lineEditGdtDateiname[i].selectAll()
                    formularOk = False
                    break
                if not self.checkBoxLoeschen[i].isChecked() and not os.path.exists(self.lineEditExportverzeichnis[i].text().strip()):
                    mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Das Exportverzeichnis für das Template \"" + self.lineEditName[i].text().strip() + "\" existiert nicht.", QMessageBox.StandardButton.Ok)
                    mb.exec()
                    formularOk = False
                    break
        if formularOk:
            self.done(1)