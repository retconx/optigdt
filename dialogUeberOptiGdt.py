from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QLabel
)
from PySide6.QtGui import Qt, QDesktopServices

class UeberOptiGdt(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Über OptiGDT")
        self.setFixedWidth(400)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.accepted.connect(self.accept) # type: ignore

        dialogLayoutV = QVBoxLayout()
        labelBeschreibung = QLabel("<span style='color:rgb(0,0,200);font-weight:bold'>Programmbeschreibung:</span><br>OptiGDT ist eine eigenständig plattformunabhängig lauffähige Software zur Optimierung von GDT-Dateien.")
        labelBeschreibung.setAlignment(Qt.AlignmentFlag.AlignJustify)
        labelBeschreibung.setWordWrap(True)
        labelBeschreibung.setTextFormat(Qt.TextFormat.RichText)
        labelEntwickeltVon = QLabel("<span style='color:rgb(0,0,200);font-weight:bold'>Entwickelt von:</span><br>Fabian Treusch<br><a href='https://gdttools.de'>gdttools.de</a>")
        labelEntwickeltVon.setTextFormat(Qt.TextFormat.RichText)
        labelEntwickeltVon.linkActivated.connect(self.gdtToolsLinkGeklickt)
        labelHilfe = QLabel("<span style='color:rgb(0,0,200);font-weight:bold'>Hilfe:</span><br><a href='https://github.com/retconx/optigdt/wiki'>OptiGDT Wiki</a>")
        labelHilfe.setTextFormat(Qt.TextFormat.RichText)
        labelHilfe.linkActivated.connect(self.githubWikiLinkGeklickt)

        dialogLayoutV.addWidget(labelBeschreibung)
        dialogLayoutV.addWidget(labelEntwickeltVon)
        dialogLayoutV.addWidget(labelHilfe)
        dialogLayoutV.addWidget(self.buttonBox)
        self.setLayout(dialogLayoutV)

    def gdtToolsLinkGeklickt(self, link):
        QDesktopServices.openUrl(link)

    def githubWikiLinkGeklickt(self, link):
        QDesktopServices.openUrl(link)