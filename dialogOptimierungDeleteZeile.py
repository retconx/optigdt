import re
from PySide6.QtGui import Qt, QFont
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QGroupBox,
    QLineEdit,
    QMessageBox,
    QLabel,
    QCheckBox
)

reFeldkennung = r"^\d{4}$"

class OptimierungDeleteZeile(QDialog):
    def __init__(self, alleVorkommen:bool=False, feldkennung:str=""):
        super().__init__()
        self.alleVorkommen = alleVorkommen
        self.feldkennung = feldkennung
        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)

        self.setWindowTitle("GDT-Optimierung: Zeile entfernen")
        self.setMinimumWidth(300)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type:ignore
        self.buttonBox.rejected.connect(self.reject) # type:ignore

        dialogLayoutV = QVBoxLayout()
        dialogLayoutG = QGridLayout()
        groupBoxZeileEntfernen = QGroupBox("Zu entfernende Zeile(n)")
        groupBoxZeileEntfernen.setFont(self.fontBold)
        groupBoxZeileEntfernen.setLayout(dialogLayoutG)
        labelFeldkennung = QLabel("Feldkennung")
        labelFeldkennung.setFont(self.fontNormal)
        self.lineEditFeldkennung = QLineEdit(self.feldkennung)
        self.lineEditFeldkennung.setFont(self.fontNormal)
        self.lineEditFeldkennung.setPlaceholderText("z. B. 6227")
        self.checkBoxAlle = QCheckBox("Alle Zeilen")
        self.checkBoxAlle.setFont(self.fontNormal)
        self.checkBoxAlle.setChecked(self.alleVorkommen)
        dialogLayoutG.addWidget(labelFeldkennung, 0, 0)
        dialogLayoutG.addWidget(self.lineEditFeldkennung, 0, 1)
        dialogLayoutG.addWidget(self.checkBoxAlle, 1, 0, 1, 2)
        
        dialogLayoutV.addWidget(groupBoxZeileEntfernen)
        dialogLayoutV.addWidget(self.buttonBox)

        self.setLayout(dialogLayoutV)
        self.lineEditFeldkennung.setFocus()
        self.lineEditFeldkennung.selectAll()

    def accept(self):
        if self.lineEditFeldkennung.text() == "" and self.lineEditFeldkennung.text() == "":
            self.done(1)
        elif not re.match(reFeldkennung, self.lineEditFeldkennung.text()):
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis", "Die Feldkennung muss aus vier Ziffern bestehen.", QMessageBox.StandardButton.Ok)
            mb.exec()
            self.lineEditFeldkennung.setFocus()
            self.lineEditFeldkennung.selectAll()
        else:
            self.done(1)