import os, re
import  class_gdtdatei
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
    QPushButton,
    QFileDialog
)

reFeldkennung = r"^\d{4}$"

class OptimierungAddPdf(QDialog):
    def __init__(self, gdtDateiOriginal:class_gdtdatei.GdtDatei, originalpfad:str="", originalname:str="", speichername:str="", dateiformat:str=""):
        super().__init__()
        self.gdtDateiOriginal = gdtDateiOriginal
        self.originalpfad = originalpfad
        self.originalname = originalname
        self.speichername = speichername
        self.dateiformat = dateiformat
        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontNormal.setItalic(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)
        self.fontBoldItalic = QFont()
        self.fontBoldItalic.setBold(True)
        self.fontBoldItalic.setItalic(True)

        self.setWindowTitle("GDT-Optimierung: PDF-Datei hinzufügen")
        self.setMinimumWidth(600)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) 
        self.buttonBox.rejected.connect(self.reject)

        dialogLayoutV = QVBoxLayout()
        dialogLayoutG = QGridLayout()
        # GroupBox Originaldatei
        groupBoxOriginaldatei = QGroupBox("Originaldatei")
        groupBoxOriginaldatei.setFont(self.fontBold)
        groupBoxOriginaldatei.setLayout(dialogLayoutG)
        labelVerzeichnis = QLabel("Verzeichnis")
        labelVerzeichnis.setFont(self.fontNormal)
        self.lineEditVerzeichnis = QLineEdit(self.originalpfad)
        self.lineEditVerzeichnis.setFont(self.fontNormal)
        self.pushButtonVerzeichnisSuchen = QPushButton("...")
        self.pushButtonVerzeichnisSuchen.setFont(self.fontNormal)
        self.pushButtonVerzeichnisSuchen.clicked.connect(self.pushbuttonVerzeichnisSuchenClicked)
        labelName = QLabel("Name (ohne \".pdf\")")
        labelName.setFont(self.fontNormal)
        self.lineEditName = QLineEdit(self.originalname)
        self.lineEditName.setFont(self.fontNormal)
        self.pushButtonVariable = QPushButton("V")
        self.pushButtonVariable.setFont(self.fontNormal)
        self.pushButtonVariable.setToolTip("Variable einfügen")
        self.pushButtonVariable.clicked.connect(lambda checked = False, lineEditName = self.lineEditName: self.pushButtonVariableClicked(checked, lineEditName))
        dialogLayoutG.addWidget(labelVerzeichnis, 0, 0)
        dialogLayoutG.addWidget(self.lineEditVerzeichnis, 0, 1)
        dialogLayoutG.addWidget(self.pushButtonVerzeichnisSuchen, 0, 2)
        dialogLayoutG.addWidget(labelName, 1, 0)
        dialogLayoutG.addWidget(self.lineEditName, 1, 1)
        dialogLayoutG.addWidget(self.pushButtonVariable, 1, 2)
        
        dialogLayoutH = QHBoxLayout()
        dialogLayoutH.setAlignment(Qt.AlignmentFlag.AlignLeft)
        groupBoxVariableEinfuegen = QGroupBox("Untersuchungsdatum/ -zeit als Variable (V) einfügen")
        groupBoxVariableEinfuegen.setFont(self.fontBoldItalic)
        groupBoxVariableEinfuegen.setLayout(dialogLayoutH)
        labelFormat = QLabel("Format")
        labelFormat.setFont(self.fontNormal)
        untersuchungsdatum = ""
        untersuchungszeit = ""
        try:
            untersuchungsdatum = gdtDateiOriginal.getInhalte("6200")[0]
        except:
            pass
        try:
            untersuchungszeit = gdtDateiOriginal.getInhalte("6201")[0]
        except:
            pass
        self.comboBoxVariable = QComboBox()
        self.comboBoxVariable.setFont(self.fontNormal)
        self.comboBoxVariable.setEditable(False)
        self.comboBoxVariable.setEnabled(False)
        self.formate= ["JJJJMMTT", "JJJJ-MM-TT", "JJJJ", "MM", "TT"]
        if untersuchungszeit != "":
            self.formate.extend(["HHmmss", "HH-mm-ss", "HH", "mm", "ss"])
        if untersuchungsdatum != "":
            self.comboBoxVariable.setEnabled(True)
            for format in self.formate:
                item = format.replace("JJJJ", untersuchungsdatum[4:]).replace("MM", untersuchungsdatum[2:4]).replace("TT", untersuchungsdatum[:2])
                if untersuchungszeit != "":
                    item = item.replace("HH", untersuchungszeit[:2]).replace("mm", untersuchungszeit[2:4]).replace("ss", untersuchungszeit[4:])
                self.comboBoxVariable.addItem(format + " (" + item + ")")
        dialogLayoutH.addWidget(labelFormat)
        dialogLayoutH.addWidget(self.comboBoxVariable)
        dialogLayoutG.addWidget(groupBoxVariableEinfuegen, 2, 0, 1, 3)

        dialogLayoutV.addWidget(groupBoxOriginaldatei)

        # GroupBox Übertragene Datei
        dialogLayoutG = QGridLayout()
        groupBoxUebertrageneDatei = QGroupBox("Übertragene Datei")
        groupBoxUebertrageneDatei.setFont(self.fontBold)
        groupBoxUebertrageneDatei.setLayout(dialogLayoutG)
        labelNameUebertragen = QLabel("Name")
        labelNameUebertragen.setFont(self.fontNormal)
        self.lineEditNameUebertragen = QLineEdit(self.speichername)
        self.lineEditNameUebertragen.setFont(self.fontNormal)
        labelDateiendung= QLabel("Dateiformatsbezeichnung\u00b9")
        labelDateiendung.setFont(self.fontNormal)
        self.lineEditDateiformat = QLineEdit(self.dateiformat)
        self.lineEditDateiformat.setFont(self.fontNormal)
        self.lineEditDateiformat.setFixedWidth(40)
        self.lineEditDateiformat.setPlaceholderText("PDF")
        labelGdtFeldkennung6303 = QLabel("(GDT-Feldkennung 6303)")
        labelGdtFeldkennung6303.setFont(self.fontNormal)
        dialogLayoutG.addWidget(labelNameUebertragen, 0, 0, 1, 1)
        dialogLayoutG.addWidget(self.lineEditNameUebertragen, 0, 1, 1, 2)
        dialogLayoutG.addWidget(labelDateiendung, 1, 0, 1, 1)
        dialogLayoutG.addWidget(self.lineEditDateiformat, 1, 1, 1, 1)
        dialogLayoutG.addWidget(labelGdtFeldkennung6303, 1, 2, 1, 1)

        dialogLayoutV.addWidget(groupBoxUebertrageneDatei)

        labelFussnote = QLabel("\u00b9 Die Dateiformatsbezeichnung hat keinen Einfluss auf das tatsächlich übertragene Dateiformat PDF.")
        labelFussnote.setFont(self.fontNormal)

        dialogLayoutV.addWidget(labelFussnote)
        dialogLayoutV.addWidget(self.buttonBox)     

        self.setLayout(dialogLayoutV)
        
    def pushbuttonVerzeichnisSuchenClicked(self):
        fd = QFileDialog(self)
        fd.setFileMode(QFileDialog.FileMode.Directory)
        fd.setWindowTitle("Verzeichnis der Originaldatei")
        if os.path.exists(self.lineEditVerzeichnis.text()):
            fd.setDirectory(self.lineEditVerzeichnis.text())
        fd.setModal(True)
        fd.setLabelText(QFileDialog.DialogLabel.Accept, "Ok")
        fd.setLabelText(QFileDialog.DialogLabel.Reject, "Abbrechen")
        if fd.exec() == 1:
            self.lineEditVerzeichnis.setText(fd.directory().path())
            self.lineEditVerzeichnis.setToolTip(fd.directory().path())

    def pushButtonVariableClicked(self, checked, lineEdit:QLineEdit):
        bisherigerInhalt = lineEdit.text()
        cursorPosition = lineEdit.cursorPosition()
        variable = "${" + self.formate[self.comboBoxVariable.currentIndex()] + "}"
        neuerInhalt = bisherigerInhalt[:cursorPosition] + variable + bisherigerInhalt[cursorPosition:]
        lineEdit.setText(neuerInhalt)
        lineEdit.setFocus()
        lineEdit.setCursorPosition(cursorPosition + len(variable))

    def accept(self):
        if self.lineEditDateiformat.text() == "":
            self.lineEditDateiformat.setText("PDF")
        if self.lineEditVerzeichnis.text() == "" or self.lineEditName.text() == "" or self.lineEditNameUebertragen.text() == "":
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Formular unvollständig ausgefüllt", QMessageBox.StandardButton.Ok)
            mb.exec()
        elif re.match(r"^[A-Za-z0-9]{3}$", self.lineEditDateiformat.text()) == None:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Die Dateiendung der übertragenen Datei muss aus drei Buchstaben (keine Umlaute) und/oder Ziffern bestehen.", QMessageBox.StandardButton.Ok)
            mb.exec()
            self.lineEditDateiformat.setFocus()
            self.lineEditDateiformat.selectAll()
        else:
            if self.lineEditName.text()[-4:].lower() == ".pdf":
                self.lineEditName.setText(self.lineEditName.text()[:-4])
            self.done(1)