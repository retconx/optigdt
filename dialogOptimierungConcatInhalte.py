import re
import class_Enums
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QGroupBox,
    QLineEdit,
    QMessageBox,
    QLabel,
    QComboBox
)

reFeldkennung = r"^\d{4}$"

class OptimierungConcatInhalte(QDialog):
    def __init__(self, feldkennung:str, einzufuegendesZeichen:class_Enums.EinzufuegendeZeichen):
        super().__init__()
        self.feldkennung = feldkennung
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
        groupBoxInhalteZusammenfuehren = QGroupBox("Zusammenzuführende Inhalte")
        groupBoxInhalteZusammenfuehren.setFont(self.fontBold)
        groupBoxInhalteZusammenfuehren.setLayout(dialogLayoutG)
        labelFeldkennung = QLabel("Feldkennung")
        labelFeldkennung.setFont(self.fontNormal)
        self.lineEditFeldkennung = QLineEdit(self.feldkennung)
        self.lineEditFeldkennung.setFont(self.fontNormal)
        self.lineEditFeldkennung.setPlaceholderText("z. B. 6220")
        labelZeichenEinfuegen = QLabel("Zeichen einfügen")
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
        dialogLayoutG.addWidget(labelZeichenEinfuegen, 1, 0)
        dialogLayoutG.addWidget(self.comboBoxZeichenEinfuegen, 1, 1)
        
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