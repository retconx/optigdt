import configparser, os
from PySide6.QtGui import QFont
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

        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)

        #config.ini lesen
        configIni = configparser.ConfigParser()
        configIni.read(os.path.join(configPath, "config.ini"))
        self.gdtImportVerzeichnisPrimaer = configIni["GDT"]["gdtimportverzeichnis"]
        if self.gdtImportVerzeichnisPrimaer == "":
            self.gdtImportVerzeichnisPrimaer = os.getcwd()
        self.gdtImportVerzeichnisSekundaer = configIni["GDT"]["gdtimportverzeichnissekundaer"]
        self.aktuelleZeichensatznummer = int(configIni["GDT"]["zeichensatz"]) - 1

        self.setWindowTitle("GDT-Einstellungen")
        self.setMinimumWidth(500)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject) 

        dialogLayoutV = QVBoxLayout()
        # Groupbox Importverzeichnis
        groupboxLayoutG = QGridLayout()
        groupboxImportverzeichnis = QGroupBox("Importverzeichnisse")
        groupboxImportverzeichnis.setFont(self.fontBold)
        labelPrimaer = QLabel("Primär")
        labelPrimaer.setFont(self.fontNormal)
        self.lineEditImportPrimaer = QLineEdit(self.gdtImportVerzeichnisPrimaer)
        self.lineEditImportPrimaer.setFont(self.fontNormal)
        buttonDurchsuchenImportPrimaer = QPushButton("Durchsuchen")
        buttonDurchsuchenImportPrimaer.setFont(self.fontNormal)
        buttonDurchsuchenImportPrimaer.clicked.connect(self.durchsuchenImportPrimaer)
        labelSekundaer = QLabel("Sekundär")
        labelSekundaer.setFont(self.fontNormal)
        self.lineEditImportSekundaer = QLineEdit(self.gdtImportVerzeichnisSekundaer)
        self.lineEditImportSekundaer.setFont(self.fontNormal)
        buttonDurchsuchenImportSekundaer = QPushButton("Durchsuchen")
        buttonDurchsuchenImportSekundaer.setFont(self.fontNormal)
        buttonDurchsuchenImportSekundaer.clicked.connect(self.durchsuchenImportSekundaer)
        groupboxLayoutG.addWidget(labelPrimaer, 0, 0)
        groupboxLayoutG.addWidget(self.lineEditImportPrimaer, 0, 1)
        groupboxLayoutG.addWidget(buttonDurchsuchenImportPrimaer, 0, 2)
        groupboxLayoutG.addWidget(labelSekundaer, 1, 0)
        groupboxLayoutG.addWidget(self.lineEditImportSekundaer, 1, 1)
        groupboxLayoutG.addWidget(buttonDurchsuchenImportSekundaer, 1, 2)
        groupboxImportverzeichnis.setLayout(groupboxLayoutG)
        # Groupbox Zeichensatz
        groupboxLayoutZeichensatz = QVBoxLayout()
        groupboxZeichensatz = QGroupBox("Zeichensatz")
        groupboxZeichensatz.setFont(self.fontBold)
        self.combobxZeichensatz = QComboBox()
        for zs in zeichensatz:
            self.combobxZeichensatz.addItem(zs)
        self.combobxZeichensatz.setFont(self.fontNormal)
        self.combobxZeichensatz.setCurrentIndex(self.aktuelleZeichensatznummer)
        self.combobxZeichensatz.currentIndexChanged.connect(self.zeichensatzGewechselt)
        groupboxLayoutZeichensatz.addWidget(self.combobxZeichensatz)
        groupboxZeichensatz.setLayout(groupboxLayoutZeichensatz)

        dialogLayoutV.addWidget(groupboxImportverzeichnis)
        dialogLayoutV.addWidget(groupboxZeichensatz)
        dialogLayoutV.addWidget(self.buttonBox)
        dialogLayoutV.setSpacing(20)
        self.setLayout(dialogLayoutV)

    def durchsuchenImportPrimaer(self):
        fd = QFileDialog(self)
        fd.setFileMode(QFileDialog.FileMode.Directory)
        fd.setWindowTitle("Primäres GDT-Importverzeichnis")
        fd.setDirectory(self.gdtImportVerzeichnisPrimaer)
        fd.setModal(True)
        fd.setLabelText(QFileDialog.DialogLabel.Accept, "Ok")
        fd.setLabelText(QFileDialog.DialogLabel.Reject, "Abbrechen")
        if fd.exec() == 1:
            self.gdtImportVerzeichnisPrimaer = fd.directory()
            self.lineEditImportPrimaer.setText(fd.directory().path())

    def durchsuchenImportSekundaer(self):
        fd = QFileDialog(self)
        fd.setFileMode(QFileDialog.FileMode.Directory)
        fd.setWindowTitle("Sekundäres GDT-Importverzeichnis")
        fd.setDirectory(self.gdtImportVerzeichnisSekundaer)
        fd.setModal(True)
        fd.setLabelText(QFileDialog.DialogLabel.Accept, "Ok")
        fd.setLabelText(QFileDialog.DialogLabel.Reject, "Abbrechen")
        if fd.exec() == 1:
            self.gdtImportVerzeichnisSekundaer = fd.directory()
            self.lineEditImportSekundaer.setText(fd.directory().path())

    def zeichensatzGewechselt(self):
        self.aktuelleZeichensatznummer = self.combobxZeichensatz.currentIndex()

    def accept(self):
        self.done(1)