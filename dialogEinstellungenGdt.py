import configparser, os
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
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

class EinstellungenGdt(QDialog):
    def __init__(self, configPath):
        super().__init__()

        #config.ini lesen
        configIni = configparser.ConfigParser()
        configIni.read(os.path.join(configPath, "config.ini"))
        self.gdtImportVerzeichnis = configIni["GDT"]["gdtimportverzeichnis"]
        if self.gdtImportVerzeichnis == "":
            self.gdtImportVerzeichnis = os.getcwd()
        self.aktuelleZeichensatznummer = int(configIni["GDT"]["zeichensatz"]) - 1

        self.setWindowTitle("GDT-Einstellungen")
        self.setMinimumWidth(500)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type:ignore
        self.buttonBox.rejected.connect(self.reject) # type:ignore

        dialogLayoutV = QVBoxLayout()
        # Groupbox Importverzeichnis
        groupboxLayoutH = QHBoxLayout()
        groupboxImportverzeichnis = QGroupBox("Importverzeichnis")
        groupboxImportverzeichnis.setStyleSheet("font-weight:bold")
        self.lineEditImport = QLineEdit(self.gdtImportVerzeichnis)
        self.lineEditImport.setStyleSheet("font-weight:normal")
        buttonDurchsuchenImport = QPushButton("Durchsuchen")
        buttonDurchsuchenImport.setStyleSheet("font-weight:normal")
        buttonDurchsuchenImport.clicked.connect(self.durchsuchenImport) # type:ignore
        groupboxLayoutH.addWidget(self.lineEditImport)
        groupboxLayoutH.addWidget(buttonDurchsuchenImport)
        groupboxImportverzeichnis.setLayout(groupboxLayoutH)
        # Groupbox Zeichensatz
        groupboxLayoutZeichensatz = QVBoxLayout()
        groupboxZeichensatz = QGroupBox("Zeichensatz")
        groupboxZeichensatz.setStyleSheet("font-weight:bold")
        self.combobxZeichensatz = QComboBox()
        for zs in zeichensatz:
            self.combobxZeichensatz.addItem(zs)
        self.combobxZeichensatz.setStyleSheet("font-weight:normal")
        self.combobxZeichensatz.setCurrentIndex(self.aktuelleZeichensatznummer)
        self.combobxZeichensatz.currentIndexChanged.connect(self.zeichensatzGewechselt) # type:ignore
        groupboxLayoutZeichensatz.addWidget(self.combobxZeichensatz)
        groupboxZeichensatz.setLayout(groupboxLayoutZeichensatz)

        dialogLayoutV.addWidget(groupboxImportverzeichnis)
        dialogLayoutV.addWidget(groupboxZeichensatz)
        dialogLayoutV.addWidget(self.buttonBox)
        dialogLayoutV.setSpacing(20)
        self.setLayout(dialogLayoutV)

    def durchsuchenImport(self):
        fd = QFileDialog(self)
        fd.setFileMode(QFileDialog.FileMode.Directory)
        fd.setWindowTitle("GDT-Importverzeichnis")
        fd.setDirectory(self.gdtImportVerzeichnis)
        fd.setModal(True)
        fd.setLabelText(QFileDialog.DialogLabel.Accept, "Ok")
        fd.setLabelText(QFileDialog.DialogLabel.Reject, "Abbrechen")
        if fd.exec() == 1:
            self.gdtImportVerzeichnis = fd.directory()
            self.lineEditImport.setText(fd.directory().path())

    def zeichensatzGewechselt(self):
        self.aktuelleZeichensatznummer = self.combobxZeichensatz.currentIndex()

    def accept(self):
        self.done(1)