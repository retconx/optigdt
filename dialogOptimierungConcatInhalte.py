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

class OptimierungConcatInhalte(QDialog):
    def __init__(self, feldkennung:str=""):
        super().__init__()
        self.feldkennung = feldkennung
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
        groupBoxInhalteZusammenfuehren = QGroupBox("Zusammenzuführende Inhalte")
        groupBoxInhalteZusammenfuehren.setFont(self.fontBold)
        groupBoxInhalteZusammenfuehren.setLayout(dialogLayoutG)
        labelFeldkennung = QLabel("Feldkennung")
        labelFeldkennung.setFont(self.fontNormal)
        self.lineEditFeldkennung = QLineEdit(self.feldkennung)
        self.lineEditFeldkennung.setFont(self.fontNormal)
        self.lineEditFeldkennung.setPlaceholderText("z. B. 6220")
        dialogLayoutG.addWidget(labelFeldkennung, 0, 0)
        dialogLayoutG.addWidget(self.lineEditFeldkennung, 0, 1)
        
        dialogLayoutV.addWidget(groupBoxInhalteZusammenfuehren)
        dialogLayoutV.addWidget(self.buttonBox)

        self.setLayout(dialogLayoutV)
        self.lineEditFeldkennung.setFocus()
        self.lineEditFeldkennung.selectAll()

    def accept(self):
        if self.lineEditFeldkennung.text() == "" and self.lineEditFeldkennung.text() == "":
            self.done(1)
        elif not re.match(reFeldkennung, self.lineEditFeldkennung.text()):
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Die Feldkennung muss aus vier Ziffern bestehen.", QMessageBox.StandardButton.Ok)
            mb.exec()
            self.lineEditFeldkennung.setFocus()
            self.lineEditFeldkennung.selectAll()
        else:
            self.done(1)