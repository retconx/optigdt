import sys, configparser, os, datetime, shutil, logger, re, time
import class_gdtdatei, gdttoolsL, class_optimierung
import xml.etree.ElementTree as ElementTree
import dialogUeberOptiGdt, dialogEinstellungenGdt, dialogEinstellungenOptimierung, dialogEinstellungenLanrLizenzschluessel, dialogOptimierungAddZeile, dialogOptimierungDeleteZeile, dialogOptimierungChangeTest, dialogOptimierungTestAus6228, dialogOptimierungBefundAusTest, dialogOptimierungConcatInhalte, dialogOptimierungDeleteTest, dialogTemplatesVerwalten, dialogOptimierungChangeZeile
from PySide6.QtCore import Qt, QTranslator, QLibraryInfo, QFileSystemWatcher
from PySide6.QtGui import QFont, QAction, QKeySequence, QIcon, QDesktopServices, QColor
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QGroupBox,
    QGridLayout,
    QCheckBox,
    QWidget,
    QLabel, 
    QPushButton,
    QLineEdit,
    QMessageBox,
    QStatusBar,
    QFileDialog, 
    QTreeWidget, 
    QTreeWidgetItem, 
    QSystemTrayIcon,
    QMenu
)
import requests

basedir = os.path.dirname(__file__)
unveraenderbareFeldkennungen = ("8000", "8100", "8315", "8316", "9206", "9218", "0102", "0103", "0132", "3000", "8402")
reKennfeld = r"^[A-Z]{1,4}[0-9]{2}$"
reGdtId = r"^[0-9A-Za-z_\-]{8}$"

# Farbdefinitionen
testauswahlHintergrund = QColor(220,220,220)
concatHintergrund = QColor(255,220,255)
addZeileHintergrund =  QColor(220,255,220)
changeZeileHintergrund = QColor(255,220,220)
changeTestHintergrund = QColor(220,220,255)
testAus6228Hintergrund = QColor(255,255,220)
befundAusTestHintergrund = QColor(220,255,255)

# Gegebenenfalls log-Verzeichnis anlegen
if not os.path.exists(os.path.join(basedir, "log")):
    os.mkdir(os.path.join(basedir, "log"), 0o777)
    logDateinummer = 0
else:
    logListe = os.listdir(os.path.join(basedir, "log"))
    logListe.sort()
    if len(logListe) > 5:
        os.remove(os.path.join(basedir, "log/" + logListe[0]))
datum = datetime.datetime.strftime(datetime.datetime.today(), "%Y%m%d")

def versionVeraltet(versionAktuell:str, versionVergleich:str):
    """
    Vergleicht zwei Versionen im Format x.x.x
    Parameter:
        versionAktuell:str
        versionVergleich:str
    Rückgabe:
        True, wenn versionAktuell veraltet
    """
    versionVeraltet= False
    hunderterBase = int(versionVergleich.split(".")[0])
    zehnerBase = int(versionVergleich.split(".")[1])
    einserBase = int(versionVergleich.split(".")[2])
    hunderter = int(versionAktuell.split(".")[0])
    zehner = int(versionAktuell.split(".")[1])
    einser = int(versionAktuell.split(".")[2])
    if hunderterBase > hunderter:
        versionVeraltet = True
    elif hunderterBase == hunderter:
        if zehnerBase >zehner:
            versionVeraltet = True
        elif zehnerBase == zehner:
            if einserBase > einser:
                versionVeraltet = True
    return versionVeraltet

# Sicherstellen, dass Icon in Windows angezeigt wird
try:
    from ctypes import windll # type: ignore
    mayappid = "gdttools.optigdt"
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(mayappid)
except ImportError:
    pass

class MainWindow(QMainWindow):
    # Mainwindow zentrieren
    def resizeEvent(self, e):
        mainwindowBreite = e.size().width()
        mainwindowHoehe = e.size().height()
        ag = self.screen().availableGeometry()
        screenBreite = ag.size().width()
        screenHoehe = ag.size().height()
        left = screenBreite / 2 - mainwindowBreite / 2
        top = screenHoehe / 2 - mainwindowHoehe / 2
        self.setGeometry(left, top, mainwindowBreite, mainwindowHoehe)

    def closeEvent(self, e):
        if self.ungesichertesTemplate:
            mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Beim Beenden des Programms gehen derzeit nicht gesicherte Daten verloren.\nSoll OptiGDT dennoch beendet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            mb.setDefaultButton(QMessageBox.StandardButton.Yes)
            mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
            mb.button(QMessageBox.StandardButton.No).setText("Nein")
            if mb.exec() == QMessageBox.StandardButton.No:
                e.ignore()
        if self.ueberwachungAktiv:
            mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Die GDT-Verzeichnisübrewachung ist aktiv.\nSoll OptiGDT dennoch beendet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            mb.setDefaultButton(QMessageBox.StandardButton.Yes)
            mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
            mb.button(QMessageBox.StandardButton.No).setText("Nein")
            if mb.exec() == QMessageBox.StandardButton.No:
                e.ignore()

    def showEvent(self, e):
        self.activateWindow()

    def __init__(self):
        super().__init__()
        self.tray = QSystemTrayIcon(app)
        icon = QIcon(os.path.join(basedir, "icons/program.png"))
        self.tray.setIcon(icon)
        self.tray.setToolTip("OptiGDT-Überwachung inaktiv")
        self.trayMenu = QMenu()
        self.trayMenuZeigenAction = QAction("OptiGDT zeigen", self)
        self.trayMenuZeigenAction.setEnabled(False)
        self.trayMenuBeendenAction = QAction("OptiGDT beenden", self)
        self.trayMenu.addAction(self.trayMenuZeigenAction)
        self.trayMenu.addAction(self.trayMenuBeendenAction)
        self.trayMenuZeigenAction.triggered.connect(self.trayMenuZeigen) # type: ignore
        self.trayMenuBeendenAction.triggered.connect(self.trayMenuBeenden) # type: ignore
        self.tray.setContextMenu(self.trayMenu)
        self.tray.show()
        self.templateRootElement = ElementTree.Element("root")
        self.templateRootElement.set("kennfeld", "")
        self.templateRootElement.set("gdtDateiname", "")
        self.templateRootElement.set("gdtIdGeraet", "")
        self.templateRootElement.set("exportverzeichnis", "")
        self.gdtDateipfad = ""
        self.ungesichertesTemplate = False
        self.optimierungsIds = {} # key: TreeViewOptimiert-Zeile:str.strip(), value: Optimierungs-Id:str
        self.ueberwachungAktiv = False

        # config.ini lesen
        ersterStart = False
        updateSafePath = ""
        if sys.platform == "win32":
            logger.logger.info("Plattform: win32")
            updateSafePath = os.path.expanduser("~\\appdata\\local\\optigdt")
        else:
            logger.logger.info("Plattform: nicht win32")
            updateSafePath = os.path.expanduser("~/.config/optigdt")
        self.configPath = updateSafePath
        self.configIni = configparser.ConfigParser()
        if os.path.exists(os.path.join(updateSafePath, "config.ini")):
            logger.logger.info("config.ini in " + updateSafePath + " exisitert")
            self.configPath = updateSafePath
        elif os.path.exists(os.path.join(basedir, "config.ini")):
            logger.logger.info("config.ini in " + updateSafePath + " exisitert nicht")
            try:
                if not os.path.exists(updateSafePath):
                    logger.logger.info(updateSafePath + " exisitert nicht")
                    os.makedirs(updateSafePath, 0o777)
                    logger.logger.info(updateSafePath + "erzeugt")
                shutil.copy(os.path.join(basedir, "config.ini"), updateSafePath)
                logger.logger.info("config.ini von " + basedir + " nach " + updateSafePath + " kopiert")
                self.configPath = updateSafePath
                ersterStart = True
            except:
                logger.logger.error("Problem beim Kopieren der config.ini von " + basedir + " nach " + updateSafePath)
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Problem beim Kopieren der Konfigurationsdatei. OptiGDT wird mit Standardeinstellungen gestartet.", QMessageBox.StandardButton.Ok)
                mb.exec()
                self.configPath = basedir
        else:
            logger.logger.critical("config.ini fehlt")
            mb = QMessageBox(QMessageBox.Icon.Critical, "Hinweis von OptiGDT", "Die Konfigurationsdatei config.ini fehlt. OptiGDT kann nicht gestartet werden.", QMessageBox.StandardButton.Ok)
            mb.exec()
            sys.exit()

        self.configIni.read(os.path.join(self.configPath, "config.ini"))
        self.gdtImportVerzeichnis = self.configIni["GDT"]["gdtimportverzeichnis"]
        self.version = self.configIni["Allgemein"]["version"]
        z = self.configIni["GDT"]["zeichensatz"]
        self.zeichensatz = class_gdtdatei.GdtZeichensatz.IBM_CP437
        if z == "1":
            self.zeichensatz = class_gdtdatei.GdtZeichensatz.BIT_7
        elif z == "3":
            self.zeichensatz = class_gdtdatei.GdtZeichensatz.ANSI_CP1252
        self.maxeindeutigkeitskriterien = int(self.configIni["Optimierung"]["maxeindeutigkeitskriterien"])
        self.maxtestaenderungen = int(self.configIni["Optimierung"]["maxtestaenderungen"])
        self.maxAnzahl6228Spalten = int(self.configIni["Optimierung"]["maxanzahl6228spalten"])
        self.standard6228trennregexpattern = self.configIni["Optimierung"]["standard6228trennregexpattern"]
        self.sekundenBisTemplatebearbeitung = int(self.configIni["Optimierung"]["sekundenbistemplatebearbeitung"])
        self.standardTemplateVerzeichnis = self.configIni["Optimierung"]["standardtemplateverzeichnis"]
        self.lanr = self.configIni["Erweiterungen"]["lanr"]
        self.lizenzschluessel = self.configIni["Erweiterungen"]["lizenzschluessel"]
        self.gdtDateiOriginal = class_gdtdatei.GdtDatei(self.zeichensatz)
        self.gdtDateiOptimiert = class_gdtdatei.GdtDatei(self.zeichensatz)

        # Nachträglich hinzufefügte Options
        # 1.1.0
        # /Nachträglich hinzufefügte Options

        # Prüfen, ob Lizenzschlüssel unverschlüsselt
        if len(self.lizenzschluessel) == 29:
            logger.logger.info("Lizenzschlüssel unverschlüsselt")
            self.configIni["Erweiterungen"]["lizenzschluessel"] = gdttoolsL.GdtToolsLizenzschluessel.krypt(self.lizenzschluessel)
            with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                    self.configIni.write(configfile)
        else:
            self.lizenzschluessel = gdttoolsL.GdtToolsLizenzschluessel.dekrypt(self.lizenzschluessel)

        # Grundeinstellungen bei erstem Start
        if ersterStart:
            logger.logger.info("Erster Start")
            mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Vermutlich starten Sie OptiGDT das erste Mal auf diesem PC.\nMöchten Sie jetzt die Grundeinstellungen vornehmen?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            mb.setDefaultButton(QMessageBox.StandardButton.Yes)
            if mb.exec() == QMessageBox.StandardButton.Yes:
                self.einstellungenOptimierung(False, neustartfrage=False)
                self.einstellungenGdt(False, neustartfrage=False)
                self.einstellungenLanrLizenzschluessel(False, neustartfrage=True)

        # Version vergleichen und gegebenenfalls aktualisieren
        configIniBase = configparser.ConfigParser()
        try:
            configIniBase.read(os.path.join(basedir, "config.ini"))
            if versionVeraltet(self.version, configIniBase["Allgemein"]["version"]):
                # Version aktualisieren
                self.configIni["Allgemein"]["version"] = configIniBase["Allgemein"]["version"]
                self.configIni["Allgemein"]["releasedatum"] = configIniBase["Allgemein"]["releasedatum"] 
                # config.ini aktualisieren
                # 1.0.3 -> 1.1.0: ["Allgemein"]["vorlagenverzeichnis"] hinzufügen

                # /config.ini aktualisieren

                with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                    self.configIni.write(configfile)
                self.version = self.configIni["Allgemein"]["version"]
                logger.logger.info("Version auf " + self.version + " aktualisiert")
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "OptiGDT wurde erfolgreich auf Version " + self.version + " aktualisiert.", QMessageBox.StandardButton.Ok)
                mb.setTextFormat(Qt.TextFormat.RichText)
                mb.exec()
        except:
            logger.logger.error("Problem beim Aktualisieren auf Version " + configIniBase["Allgemein"]["version"])
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Problem beim Aktualisieren auf Version " + configIniBase["Allgemein"]["version"], QMessageBox.StandardButton.Ok)
            mb.exec()

        # Add-Ons freigeschaltet?
        self.addOnsFreigeschaltet = gdttoolsL.GdtToolsLizenzschluessel.lizenzErteilt(self.lizenzschluessel, self.lanr, gdttoolsL.SoftwareId.OPTIGDT)
        
        jahr = datetime.datetime.now().year
        copyrightJahre = "2023"
        if jahr > 2023:
            copyrightJahre = "2023-" + str(jahr)
        self.setWindowTitle("OptiGDT V" + self.version + " (\u00a9 Fabian Treusch - GDT-Tools " + copyrightJahre + ")")
        self.setMinimumSize(1200,800)
        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)
        self.fontKlein = QFont()
        self.fontKlein.setPixelSize(10)
        self.fontDurchgestrichen = QFont()
        self.fontDurchgestrichen.setStrikeOut(True)

        widget = QWidget()
        mainVerticalLayout = QVBoxLayout()
        mainGridLayout = QGridLayout()
        optimierungsButtonsLayout = QVBoxLayout()

        self.labelTreeViewUeberschriftLinks = QLabel("Original:")
        self.labelTreeViewUeberschriftLinks.setFont(self.fontBold)
        self.labelTreeViewUeberschriftRechts = QLabel("Optimiert:")
        self.labelTreeViewUeberschriftRechts.setFont(self.fontBold)

        self.treeWidgetOriginal = QTreeWidget()
        self.treeWidgetOriginal.setColumnCount(3)
        self.treeWidgetOriginal.setHeaderLabels(["Zeile", "Feldkennung", "Inhalt"])
        self.treeWidgetOriginal.currentItemChanged.connect(self.treeWidgetCurrentItemChanged) # type:ignore

        self.treeWidgetOptimiert = QTreeWidget()
        self.treeWidgetOptimiert.setColumnCount(3)
        self.treeWidgetOptimiert.setHeaderLabels(["Zeile", "Feldkennung", "Inhalt"])
        self.treeWidgetOptimiert.currentItemChanged.connect(self.treeWidgetCurrentItemChanged) # type:ignore

        # Contextmenü
        self.treeWidgetOptimiert.setContextMenuPolicy(Qt.ActionsContextMenu) # type:ignore
        self.optimierungBearbeitenAction = QAction("Optimierung bearbeiten", self)
        self.optimierungBearbeitenAction.triggered.connect(self.optimierungBearbeiten) # type:ignore
        self.treeWidgetOptimiert.addAction(self.optimierungBearbeitenAction)
        self.optimierungEntfernenAction = QAction("Optimierung entfernen", self)
        self.optimierungEntfernenAction.triggered.connect(self.optimierungEntfernen) # type:ignore
        self.treeWidgetOptimiert.addAction(self.optimierungEntfernenAction)

        # Optimierungsbuttons
        labelOptimierungen = QLabel("Optimierung:")
        labelOptimierungen.setFont(self.fontBold)
        self.pushButtonZeileHinzufuegen = QPushButton("Zeile hinzufügen")
        self.pushButtonZeileHinzufuegen.setFont(self.fontNormal)
        self.pushButtonZeileHinzufuegen.clicked.connect(lambda checked=False, optimierungsId="": self.optimierenMenuZeileHinzufuegen(checked, optimierungsId)) # type: ignore
        self.pushButtonZeileAendern = QPushButton("Zeile ändern")
        self.pushButtonZeileAendern.setFont(self.fontNormal)
        self.pushButtonZeileAendern.clicked.connect(lambda checked=False, optimierungsId="": self.optimierenMenuZeileAendern(checked, optimierungsId)) # type: ignore
        self.pushButtonZeileEntfernen = QPushButton("Zeile entfernen")
        self.pushButtonZeileEntfernen.setFont(self.fontNormal)
        self.pushButtonZeileEntfernen.clicked.connect(lambda checked=False, optimierungsId="": self.optimierenMenuZeileEntfernen(checked, optimierungsId)) # type: ignore
        self.pushButtonTestAendern = QPushButton("Test ändern")
        self.pushButtonTestAendern.setFont(self.fontNormal)
        self.pushButtonTestAendern.clicked.connect(lambda checked=False, optimierungsId="": self.optimierenMenuTestAendern(checked, optimierungsId)) # type: ignore
        self.pushButtonTestEntfernen = QPushButton("Test entfernen")
        self.pushButtonTestEntfernen.setFont(self.fontNormal)
        self.pushButtonTestEntfernen.clicked.connect(lambda checked=False, optimierungsId="": self.optimierenMenuTestEntfernen(checked, optimierungsId)) # type: ignore
        self.pushButtonTestAus6228 = QPushButton("Test aus 6228-Zeile")
        self.pushButtonTestAus6228.setFont(self.fontNormal)
        self.pushButtonTestAus6228.clicked.connect(lambda checked=False, optimierungsId="": self.optimierenMenuTestAus6228(checked, optimierungsId)) # type: ignore
        self.pushButtonBefundAusTest = QPushButton("Befund aus Test")
        self.pushButtonBefundAusTest.setFont(self.fontNormal)
        self.pushButtonBefundAusTest.clicked.connect(lambda checked=False, optimierungsId="": self.optimierenMenuBefundAusTest(checked, optimierungsId)) # type: ignore
        self.pushButtonInhalteZusammenfuehren = QPushButton("Inhalte zusammenführen")
        self.pushButtonInhalteZusammenfuehren.setFont(self.fontNormal)
        self.pushButtonInhalteZusammenfuehren.clicked.connect(lambda checked=False, optimierungsId="": self.optimierenMenuInhalteZusammenfuehren(checked, optimierungsId)) # type: ignore

        # Template-Infos
        templateInfosLayout = QGridLayout()
        groupBoxTemplateInfos = QGroupBox("Template-Infos")
        groupBoxTemplateInfos.setFont(self.fontBold)
        groupBoxTemplateInfos.setLayout(templateInfosLayout)
        labelName = QLabel("Name")
        labelName.setFont(self.fontNormal)
        self.lineEditName = QLineEdit()
        self.lineEditName.setFont(self.fontNormal)
        self.lineEditName.textEdited.connect(self.lineEditTemplateInfoChanged) # type: ignore
        labelKennfeld = QLabel("Gerätespezifisches Kennfeld")
        labelKennfeld.setFont(self.fontNormal)
        self.lineEditKennfeld = QLineEdit()
        self.lineEditKennfeld.setFont(self.fontNormal)
        self.lineEditKennfeld.textEdited.connect(self.lineEditTemplateInfoChanged) # type: ignore
        labelGdtId = QLabel("GDT-ID")
        labelGdtId.setFont(self.fontNormal)
        self.lineEditGdtId = QLineEdit()
        self.lineEditGdtId.setFont(self.fontNormal)
        self.lineEditGdtId.textEdited.connect(self.lineEditTemplateInfoChanged) # type: ignore
        labelGdtDateiname = QLabel("GDT-Dateiname")
        labelGdtDateiname.setFont(self.fontNormal)
        self.lineEditGdtDateiname = QLineEdit()
        self.lineEditGdtDateiname.setFont(self.fontNormal)
        self.lineEditGdtDateiname.textEdited.connect(self.lineEditTemplateInfoChanged) # type: ignore
        labelExportverzeichnis = QLabel("Exportverzeichnis")
        labelExportverzeichnis.setFont(self.fontNormal)
        self.lineEditExportverzeichnis = QLineEdit()
        self.lineEditExportverzeichnis.setFont(self.fontNormal)
        self.lineEditExportverzeichnis.setReadOnly(True)
        self.lineEditExportverzeichnis.textChanged.connect(self.lineEditTemplateInfoChanged) # type: ignore
        self.checkBoxKennfeld = QCheckBox("PR\u00b9")
        self.checkBoxKennfeld.setFont(self.fontNormal)
        self.checkBoxKennfeld.setToolTip("Prüfungsrelevant")
        self.checkBoxKennfeld.stateChanged.connect(self.checkBoxKennfeldChanged) # type: ignore
        self.checkBoxGdtId = QCheckBox("PR\u00b9")
        self.checkBoxGdtId.setFont(self.fontNormal)
        self.checkBoxGdtId.setToolTip("Prüfungsrelevant")
        self.checkBoxGdtId.stateChanged.connect(self.checkBoxGdtIdChanged) # type: ignore
        self.pushButtonExportverzeichnis = QPushButton("...")
        self.pushButtonExportverzeichnis.setFont(self.fontNormal)
        self.pushButtonExportverzeichnis.setToolTip("Durchsuchen")
        self.pushButtonExportverzeichnis.clicked.connect(self.pushButtonExportverzeichnisClicked) # type: ignore
        labelFussnote1 = QLabel("\u00b9 Prüfungsrelevant: wird vor Anwendung des Templates auf Übereinstimmung geprüft")
        labelFussnote1.setFont(self.fontNormal)

        templateInfosLayout.addWidget(labelName, 0, 0)
        templateInfosLayout.addWidget(self.lineEditName, 0, 1)
        templateInfosLayout.addWidget(labelKennfeld, 1, 0)
        templateInfosLayout.addWidget(self.lineEditKennfeld, 1, 1)
        templateInfosLayout.addWidget(self.checkBoxKennfeld, 1, 2)
        templateInfosLayout.addWidget(labelGdtId, 2, 0)
        templateInfosLayout.addWidget(self.lineEditGdtId, 2, 1)
        templateInfosLayout.addWidget(self.checkBoxGdtId, 2, 2)
        templateInfosLayout.addWidget(labelGdtDateiname, 3, 0)
        templateInfosLayout.addWidget(self.lineEditGdtDateiname, 3, 1)
        # templateInfosLayout.addWidget(self.checkBoxGdtDateiname, 3, 2)
        templateInfosLayout.addWidget(labelExportverzeichnis, 4, 0)
        templateInfosLayout.addWidget(self.lineEditExportverzeichnis, 4, 1)
        templateInfosLayout.addWidget(self.pushButtonExportverzeichnis, 4, 2)
        templateInfosLayout.addWidget(labelFussnote1, 5, 0, 1, 2)

        mainGridLayout.addWidget(self.labelTreeViewUeberschriftLinks, 0, 0)
        mainGridLayout.addWidget(self.labelTreeViewUeberschriftRechts, 0, 1)
        mainGridLayout.addWidget(labelOptimierungen, 0, 2)
        mainGridLayout.addWidget(self.treeWidgetOriginal, 1, 0)
        mainGridLayout.addWidget(self.treeWidgetOptimiert, 1, 1)
        optimierungsButtonsLayout.addWidget(self.pushButtonZeileHinzufuegen)
        optimierungsButtonsLayout.addWidget(self.pushButtonZeileAendern)
        optimierungsButtonsLayout.addWidget(self.pushButtonZeileEntfernen)
        optimierungsButtonsLayout.addWidget(self.pushButtonTestAendern)
        optimierungsButtonsLayout.addWidget(self.pushButtonTestEntfernen)
        optimierungsButtonsLayout.addWidget(self.pushButtonTestAus6228)
        optimierungsButtonsLayout.addWidget(self.pushButtonBefundAusTest)
        optimierungsButtonsLayout.addWidget(self.pushButtonInhalteZusammenfuehren)
        mainGridLayout.addLayout(optimierungsButtonsLayout, 1, 2, alignment=Qt.AlignmentFlag.AlignTop)

        # Überwachung starten-Button
        self.pushButtonUeberwachungStarten = QPushButton("Verzeichnisüberwachung starten")
        self.pushButtonUeberwachungStarten.setFont(self.fontBold)
        self.pushButtonUeberwachungStarten.setCheckable(True)
        self.pushButtonUeberwachungStarten.setFixedHeight(40)
        self.pushButtonUeberwachungStarten.setStyleSheet("background:rgb(0,50,0);color:rgb(255,255,255);border:2px solid rgb(0,0,0)")
        self.pushButtonUeberwachungStarten.clicked.connect(self.pushButtonUeberwachungStartenClicked) # type: ignore
        
        # Statusleiste
        self.statusleiste = QStatusBar()
        self.statusleiste.setFont(self.fontKlein)

        mainVerticalLayout.addLayout(mainGridLayout)
        mainVerticalLayout.addWidget(groupBoxTemplateInfos)
        mainVerticalLayout.addWidget(self.pushButtonUeberwachungStarten)
        mainVerticalLayout.addWidget(self.statusleiste)

        widget.setLayout(mainVerticalLayout)
        self.setCentralWidget(widget)
        
        self.optimierungBearbeitenAction.setEnabled(False)
        self.optimierungEntfernenAction.setEnabled(False)

        logger.logger.info("Eingabeformular aufgebaut")

        # Menü
        menubar = self.menuBar()
        anwendungMenu = menubar.addMenu("")
        aboutAction = QAction(self)
        aboutAction.setMenuRole(QAction.MenuRole.AboutRole)
        aboutAction.triggered.connect(self.ueberOptiGdt) # type: ignore
        updateAction = QAction("Auf Update prüfen", self)
        updateAction.setMenuRole(QAction.MenuRole.ApplicationSpecificRole)
        updateAction.triggered.connect(self.updatePruefung) # type: ignore
        gdtDateiMenu = menubar.addMenu("GDT-Datei")
        gdtDateiMenuOeffnenAction = QAction("Öffnen", self)
        gdtDateiMenuOeffnenAction.triggered.connect(self.gdtDateiMenuOeffnen) # type:ignore
        gdtDateiMenuOeffnenAction.setShortcut(QKeySequence("Ctrl+G"))
        templateMenu = menubar.addMenu("Template")
        templateMenuLadenAction = QAction("Laden", self)
        templateMenuLadenAction.triggered.connect(self.templateMenuLaden) # type:ignore
        templateMenuLadenAction.setShortcut(QKeySequence("Ctrl+T"))
        templateMenuSpeichernAction = QAction("Speichern", self)
        templateMenuSpeichernAction.triggered.connect(self.templateMenuSpeichern) # type:ignore
        templateMenuTemplatesVerwaltenAction = QAction("Templates verwalten", self)
        templateMenuTemplatesVerwaltenAction.triggered.connect(self.templateMenuTemplatesVerwalten) # type: ignore
        optimierenMenu = menubar.addMenu("Optimieren")
        optimierenMenuZeileHinzufuegenAction = QAction("Zeile hinzufügen", self)
        optimierenMenuZeileHinzufuegenAction.triggered.connect(lambda checked=False, optimierungsId="": self.optimierenMenuZeileHinzufuegen(checked, optimierungsId)) # type:ignore
        optimierenMenuZeileAendernAction = QAction("Zeile ändern", self)
        optimierenMenuZeileAendernAction.triggered.connect(lambda checked=False, optimierungsId="": self.optimierenMenuZeileAendern(checked, optimierungsId)) # type:ignore
        optimierenMenuZeileEntfernenAction = QAction("Zeile entfernen", self)
        optimierenMenuZeileEntfernenAction.triggered.connect(lambda checked=False, optimierungsId="": self.optimierenMenuZeileEntfernen(checked, optimierungsId)) # type:ignore
        optimierenMenuTestAendernAction = QAction("Test ändern", self)
        optimierenMenuTestAendernAction.triggered.connect(lambda checked=False, optimierungsId="": self.optimierenMenuTestAendern(checked, optimierungsId)) # type:ignore
        optimierenMenuTestEntfernenAction = QAction("Test entfernen", self)
        optimierenMenuTestEntfernenAction.triggered.connect(lambda checked=False, optimierungsId="": self.optimierenMenuTestEntfernen(checked, optimierungsId)) # type:ignore
        optimierenMenuTestAus6228Action = QAction("Test aus 6228-Zeile", self)
        optimierenMenuTestAus6228Action.triggered.connect(lambda checked=False, optimierungsId="": self.optimierenMenuTestAus6228(checked, optimierungsId)) # type:ignore
        optimierenMenuBefundAusTestAction = QAction("Befundzeile aus Test(s)", self)
        optimierenMenuBefundAusTestAction.triggered.connect(lambda checked=False, optimierungsId="": self.optimierenMenuBefundAusTest(checked, optimierungsId)) # type:ignore
        optimierenMenuInhalteZusammenfuehrenAction = QAction("Inhalte zusammenführen", self)
        optimierenMenuInhalteZusammenfuehrenAction.triggered.connect(lambda checked=False, optimierungsId="": self.optimierenMenuInhalteZusammenfuehren(checked, optimierungsId)) # type:ignore

        einstellungenMenu = menubar.addMenu("Einstellungen")
        einstellungenOptimierungAction = QAction("Optimierung", self)
        einstellungenOptimierungAction.triggered.connect(lambda checked=False, neustartfrage=True: self.einstellungenOptimierung(checked, neustartfrage)) # type: ignore
        einstellungenGdtAction = QAction("GDT", self)
        einstellungenGdtAction.triggered.connect(lambda checked=False, neustartfrage=True: self.einstellungenGdt(checked, neustartfrage)) # type: ignore
        einstellungenErweiterungenAction = QAction("LANR/Lizenzschlüssel", self)
        einstellungenErweiterungenAction.triggered.connect(lambda checked=False, neustartfrage=True: self.einstellungenLanrLizenzschluessel(checked, neustartfrage)) # type: ignore
        hilfeMenu = menubar.addMenu("Hilfe")
        hilfeWikiAction = QAction("OptiGDT Wiki", self)
        hilfeWikiAction.triggered.connect(self.optigdtWiki) # type: ignore
        hilfeUpdateAction = QAction("Auf Update prüfen", self)
        hilfeUpdateAction.triggered.connect(self.updatePruefung) # type: ignore
        hilfeUeberAction = QAction("Über OptiGDT", self)
        hilfeUeberAction.setMenuRole(QAction.MenuRole.NoRole)
        hilfeUeberAction.triggered.connect(self.ueberOptiGdt) # type: ignore
        hilfeLogExportieren = QAction("Log-Verzeichnis exportieren", self)
        hilfeLogExportieren.triggered.connect(self.logExportieren) # type: ignore
        
        anwendungMenu.addAction(aboutAction)
        anwendungMenu.addAction(updateAction)

        gdtDateiMenu.addAction(gdtDateiMenuOeffnenAction)
        templateMenu.addAction(templateMenuLadenAction)
        templateMenu.addAction(templateMenuSpeichernAction)
        templateMenu.addAction(templateMenuTemplatesVerwaltenAction)
        optimierenMenu.addAction(optimierenMenuZeileHinzufuegenAction)
        optimierenMenu.addAction(optimierenMenuZeileAendernAction)
        optimierenMenu.addAction(optimierenMenuZeileEntfernenAction)
        optimierenMenu.addAction(optimierenMenuTestAendernAction)
        optimierenMenu.addAction(optimierenMenuTestEntfernenAction)
        optimierenMenu.addAction(optimierenMenuTestAus6228Action)
        optimierenMenu.addAction(optimierenMenuBefundAusTestAction)
        optimierenMenu.addAction(optimierenMenuInhalteZusammenfuehrenAction)
        einstellungenMenu.addAction(einstellungenOptimierungAction)
        einstellungenMenu.addAction(einstellungenGdtAction)
        einstellungenMenu.addAction(einstellungenErweiterungenAction)

        hilfeMenu.addAction(hilfeWikiAction)
        hilfeMenu.addSeparator()
        hilfeMenu.addAction(hilfeUpdateAction)
        hilfeMenu.addSeparator()
        hilfeMenu.addAction(hilfeUeberAction)
        hilfeMenu.addSeparator()
        hilfeMenu.addAction(hilfeLogExportieren)

        # Updateprüfung auf Github
        try:
            self.updatePruefung(meldungNurWennUpdateVerfuegbar=True)
        except Exception as e:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Updateprüfung nicht möglich.\nBitte überprüfen Sie Ihre Internetverbindung.", QMessageBox.StandardButton.Ok)
            mb.exec()
            logger.logger.warning("Updateprüfung nicht möglich: " + str(e))
        
        if len(sys.argv) > 1 and "bg" in sys.argv:
            self.pushButtonUeberwachungStarten.setChecked(True)
            self.pushButtonUeberwachungStartenClicked(True)

    def AddOnsFreigeschaltet(self):
        return self.addOnsFreigeschaltet

    def setStatusMessage(self, message = ""):
        self.statusleiste.clearMessage()
        if message != "":
            self.statusleiste.showMessage("Statusmeldung: " + message)
            logger.logger.info("Statusmessage: " + message)

    def treeWidgetAusfuellen(self, treeWidget:QTreeWidget, gdtDatei:class_gdtdatei.GdtDatei):
        """
        Füllt das TreeWidget neu
        Parameter:
            treeWidget:QTreeWidget
            gdtDatei:class_gdtdatei.GdtDatei
        """
        treeWidget.clear()
        regexOptiKennzeichnung = r"__\d{4}__"
        self.optimierungsIds.clear()
        zeilennummer = 1
        for zeile in gdtDatei.getZeilen():
            item = QTreeWidgetItem()
            item.setText(0, "{:>3}".format(str(zeilennummer)))
            item.setText(1, zeile[3:7])
            if re.match(regexOptiKennzeichnung, zeile[-8:]) != None:
                id = str(int(zeile[-6:-2]))
                typ = class_optimierung.Optimierung.getTypVonId(self.templateRootElement, id)
                item.setText(2, zeile[7:-8])
                if typ == "addZeile":
                    self.setTreeWidgetItemHintergrund(item, treeWidget.columnCount(), addZeileHintergrund)
                elif typ == "changeZeile":
                    self.setTreeWidgetItemHintergrund(item, treeWidget.columnCount(), changeZeileHintergrund)
                elif typ == "deleteZeile":
                    item.setFont(2, self.fontDurchgestrichen)
                elif typ == "deleteTest":
                    item.setFont(2, self.fontDurchgestrichen)
                elif typ == "changeTest":
                    self.setTreeWidgetItemHintergrund(item, treeWidget.columnCount(), changeTestHintergrund)
                elif typ == "testAus6228":
                    self.setTreeWidgetItemHintergrund(item, treeWidget.columnCount(), testAus6228Hintergrund)
                elif typ == "befundAusTest":
                    self.setTreeWidgetItemHintergrund(item, treeWidget.columnCount(), befundAusTestHintergrund)
                elif typ == "concatInhalte":
                    self.setTreeWidgetItemHintergrund(item, treeWidget.columnCount(), concatHintergrund)
                self.optimierungsIds[str(zeilennummer).strip()] = id
            else:
                item.setText(2, zeile[7:])
            zeilennummer += 1
            treeWidget.addTopLevelItem(item)
            self.treeWidgetOptimiert.addTopLevelItem(item)
        treeWidget.resizeColumnToContents(0)
        treeWidget.resizeColumnToContents(1)
        treeWidget.resizeColumnToContents(2)
    
    def treeWidgetCurrentItemChanged(self, current, previous):
        if current:
            # Contextmenus (de)aktivieren
            self.optimierungBearbeitenAction.setEnabled(current.text(0).strip() in self.optimierungsIds)
            self.optimierungEntfernenAction.setEnabled(current.text(0).strip() in self.optimierungsIds)
            treeWidget = current.treeWidget()
            # Farbiger Hintergrund für Tests
            for index in range(treeWidget.topLevelItemCount()):
                if treeWidget.topLevelItem(index).background(0).color() == testauswahlHintergrund:
                    self.setTreeWidgetZeileHintergrund(treeWidget, index, QColor(255,255,255))
            itemIndex = int(current.text(0)) - 1
            currentFeldkennung = current.text(1)
            ersteTestItemNummer = itemIndex
            letzteTestItemNummer = itemIndex
            istTest = False # 8410 vorhanden?
            if currentFeldkennung[0:2] == "84":
                if currentFeldkennung != "8410":
                    tempFeldkennung = currentFeldkennung
                    while ersteTestItemNummer > 0 and tempFeldkennung[0:2] == "84" and tempFeldkennung != "8410":
                        ersteTestItemNummer -= 1
                        tempFeldkennung = treeWidget.topLevelItem(ersteTestItemNummer).text(1)
                    if tempFeldkennung == "8410":
                        istTest = True
                else:
                    istTest = True
                    letzteTestItemNummer += 1
                tempFeldkennung = treeWidget.topLevelItem(letzteTestItemNummer).text(1)
                while letzteTestItemNummer < treeWidget.topLevelItemCount() - 1 and tempFeldkennung[0:2] == "84" and tempFeldkennung != "8410":
                    letzteTestItemNummer += 1
                    tempFeldkennung = treeWidget.topLevelItem(letzteTestItemNummer).text(1)
                if istTest:
                    for i in range(letzteTestItemNummer - ersteTestItemNummer):
                        if treeWidget.topLevelItem(i + ersteTestItemNummer).background(0).color() != changeTestHintergrund and treeWidget.topLevelItem(i + ersteTestItemNummer).background(0).color() != testAus6228Hintergrund:
                            self.setTreeWidgetZeileHintergrund(treeWidget, i + ersteTestItemNummer, testauswahlHintergrund)
        else:
            self.optimierungBearbeitenAction.setEnabled(False)
            self.optimierungEntfernenAction.setEnabled(False)

    def lineEditTemplateInfoChanged(self):
        self.ungesichertesTemplate = True

    def pushButtonExportverzeichnisClicked(self):
        fd = QFileDialog(self)
        fd.setFileMode(QFileDialog.FileMode.Directory)
        fd.setWindowTitle("Exportverzeichnis")
        if os.path.exists(self.lineEditExportverzeichnis.text()):
            fd.setDirectory(self.lineEditExportverzeichnis.text())
        fd.setModal(True)
        fd.setLabelText(QFileDialog.DialogLabel.Accept, "Ok")
        fd.setLabelText(QFileDialog.DialogLabel.Reject, "Abbrechen")
        if fd.exec() == 1:
            self.lineEditExportverzeichnis.setText(fd.directory().path())
            self.lineEditExportverzeichnis.setToolTip(fd.directory().path())

    def checkBoxKennfeldChanged(self):
        self.ungesichertesTemplate = True
        if self.checkBoxKennfeld.isChecked():
            try:
                self.lineEditKennfeld.setText(self.gdtDateiOriginal.getInhalte("8402")[0])
            except:
                pass
        else:
            self.lineEditKennfeld.setText("")

    def checkBoxGdtIdChanged(self):
        self.ungesichertesTemplate = True
        if self.checkBoxGdtId.isChecked():
            try:
                self.lineEditGdtId.setText(self.gdtDateiOriginal.getInhalte("8316")[0])
            except:
                pass
        else:
            self.lineEditGdtId.setText("")

    # def checkBoxGdtDateinameChanged(self):
    #     if self.checkBoxGdtDateiname.isChecked():
    #         self.lineEditGdtDateiname.setText(os.path.basename(self.gdtDateipfad))

    # Menuverarbeitung
    def einstellungenOptimierung(self, checked, neustartfrage=False):
        de = dialogEinstellungenOptimierung.EinstellungenOptimierung(self.configPath)
        if de.exec() == 1:
            self.configIni["Optimierung"]["standardtemplateverzeichnis"] = de.lineEditTemplateverzeichnis.text().strip()
            self.configIni["Optimierung"]["sekundenbistemplatebearbeitung"] = de.lineEditVerzoegerung.text().strip()
            self.configIni["Optimierung"]["maxeindeutigkeitskriterien"] = de.lineEditMaxEindutigkeitskriterien.text().strip()
            self.configIni["Optimierung"]["maxtestaenderungen"] = de.lineEditMaxAenderungenProTest.text().strip()
            self.configIni["Optimierung"]["maxanzahl6228spalten"] = de.lineEditMaxAnzahl6228Spalten.text().strip()
            self.configIni["Optimierung"]["standard6228trennregexpattern"] = de.lineEditStandardSpaltenTrennzeichen.text().strip()

            with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                self.configIni.write(configfile)
            if neustartfrage:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Damit die Einstellungsänderungen wirksam werden, sollte OptiGDT neu gestartet werden.\nSoll OptiGDT jetzt neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    os.execl(sys.executable, __file__, *sys.argv)
        
    def einstellungenGdt(self, checked, neustartfrage=False):
        de = dialogEinstellungenGdt.EinstellungenGdt(self.configPath)
        if de.exec() == 1:
            self.configIni["GDT"]["gdtimportverzeichnis"] = de.lineEditImport.text()
            self.configIni["GDT"]["zeichensatz"] = str(de.aktuelleZeichensatznummer + 1)
            with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                self.configIni.write(configfile)
            if neustartfrage:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Damit die Einstellungsänderungen wirksam werden, sollte OptiGDT neu gestartet werden.\nSoll OptiGDT jetzt neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    os.execl(sys.executable, __file__, *sys.argv)
    
    def einstellungenLanrLizenzschluessel(self, checked, neustartfrage=False):
        de = dialogEinstellungenLanrLizenzschluessel.EinstellungenProgrammerweiterungen(self.configPath)
        if de.exec() == 1:
            self.configIni["Erweiterungen"]["lanr"] = de.lineEditLanr.text()
            self.configIni["Erweiterungen"]["lizenzschluessel"] = gdttoolsL.GdtToolsLizenzschluessel.krypt(de.lineEditLizenzschluessel.text())
            if de.lineEditLanr.text() == "" and de.lineEditLizenzschluessel.text() == "":
                self.configIni["Allgemein"]["pdferstellen"] = "0"
                self.configIni["Allgemein"]["einrichtungaufpdf"] = "0"
                self.configIni["Allgemein"]["pdfbezeichnung"] = "Dosierungsplan"
            with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                self.configIni.write(configfile)
            if neustartfrage:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Damit die Einstellungsänderungen wirksam werden, sollte OptiGDT neu gestartet werden.\nSoll OptiGDT jetzt neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    os.execl(sys.executable, __file__, *sys.argv)

    def optigdtWiki(self, link):
        QDesktopServices.openUrl("https://www.github.com/retconx/optigdt/wiki")

    def logExportieren(self):
        if (os.path.exists(os.path.join(basedir, "log"))):
            downloadPath = ""
            if sys.platform == "win32":
                downloadPath = os.path.expanduser("~\\Downloads")
            else:
                downloadPath = os.path.expanduser("~/Downloads")
            try:
                if shutil.copytree(os.path.join(basedir, "log"), os.path.join(downloadPath, "Log_OptiGDT"), dirs_exist_ok=True):
                    shutil.make_archive(os.path.join(downloadPath, "Log_OptiGDT"), "zip", root_dir=os.path.join(downloadPath, "Log_OptiGDT"))
                    shutil.rmtree(os.path.join(downloadPath, "Log_OptiGDT"))
                    mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Das Log-Verzeichnis wurde in den Ordner " + downloadPath + " kopiert.", QMessageBox.StandardButton.Ok)
                    mb.exec()
            except Exception as e:
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Problem beim Download des Log-Verzeichnisses: " + str(e), QMessageBox.StandardButton.Ok)
                mb.exec()
        else:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Das Log-Verzeichnis wurde nicht gefunden.", QMessageBox.StandardButton.Ok)
            mb.exec() 
                
    def updatePruefung(self, meldungNurWennUpdateVerfuegbar = False):
        response = requests.get("https://api.github.com/repos/retconx/optigdt/releases/latest")
        githubRelaseTag = response.json()["tag_name"]
        latestVersion = githubRelaseTag[1:] # ohne v
        if versionVeraltet(self.version, latestVersion):
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Die aktuellere OptiGDT-Version " + latestVersion + " ist auf <a href='https://www.github.com/retconx/optigdt/releases'>Github</a> verfügbar.", QMessageBox.StandardButton.Ok)
            mb.setTextFormat(Qt.TextFormat.RichText)
            mb.exec()
        elif not meldungNurWennUpdateVerfuegbar:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Sie nutzen die aktuelle OptiGDT-Version.", QMessageBox.StandardButton.Ok)
            mb.exec()
    
    def ueberOptiGdt(self):
        de = dialogUeberOptiGdt.UeberOptiGdt()
        de.exec()

    def gdtDateiMenuOeffnen(self):
        fortfahren = True
        if self.ungesichertesTemplate:
            mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Beim Öffnen einer GDT-Datei gehen derzeit nicht gesicherte Daten verloren.\nWollen Sie dennoch fortfahren?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            mb.setDefaultButton(QMessageBox.StandardButton.Yes)
            mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
            mb.button(QMessageBox.StandardButton.No).setText("Nein")
            if mb.exec() == QMessageBox.StandardButton.No:
                fortfahren = False
        if fortfahren:
            fd = QFileDialog(self)
            fd.setFileMode(QFileDialog.FileMode.ExistingFile)
            fd.setWindowTitle("GDT-Datei laden")
            fd.setModal(True)
            fd.setViewMode(QFileDialog.ViewMode.Detail)
            fd.setNameFilters(["gdt-Dateien (*.gdt)"])
            fd.setLabelText(QFileDialog.DialogLabel.Accept, "Ok")
            fd.setLabelText(QFileDialog.DialogLabel.Reject, "Abbrechen")
            if fd.exec() == 1:
                gdtDateiPfad = fd.selectedFiles()[0]
                try:
                    self.gdtDateiOriginal.laden(gdtDateiPfad)
                    self.labelTreeViewUeberschriftLinks.setText("Original (" + gdtDateiPfad + "):")
                    self.treeWidgetAusfuellen(self.treeWidgetOriginal, self.gdtDateiOriginal)
                    self.gdtDateiOptimiert.laden(gdtDateiPfad)
                    self.treeWidgetAusfuellen(self.treeWidgetOptimiert, self.gdtDateiOptimiert)
                    self.gdtDateipfad = gdtDateiPfad
                    self.lineEditName.setText("")
                    self.lineEditKennfeld.setText("")
                    self.lineEditGdtId.setText("")
                    self.lineEditGdtDateiname.setText("")
                    self.lineEditExportverzeichnis.setText("")
                    self.checkBoxKennfeld.setChecked(False)
                    self.checkBoxGdtId.setChecked(False)
                    self.templateRootElement.clear()
                    self.ungesichertesTemplate = False
                    kennfeld = ""
                    try:
                        kennfeld = self.gdtDateiOriginal.getInhalte("8402")[0]
                        self.checkBoxKennfeld.setChecked(True)
                    except:
                        logger.logger.warning("Feldkennung 8402 in GDT-Datei " + self.gdtDateipfad + " nicht vorhanden")
                    self.lineEditKennfeld.setText(kennfeld)
                    gdtId = ""
                    try:
                        gdtId = self.gdtDateiOriginal.getInhalte("8316")[0]
                        self.checkBoxGdtId.setChecked(True)
                    except:
                        logger.logger.warning("Feldkennung 8316 in GDT-Datei " + self.gdtDateipfad + " nicht vorhanden")
                    self.lineEditGdtId.setText(gdtId)
                    self.lineEditGdtDateiname.setText(os.path.basename(self.gdtDateipfad))
                    self.ungesichertesTemplate = False
                    self.setStatusMessage("GDT-Datei " + self.gdtDateipfad + " geladen")
                except class_gdtdatei.GdtFehlerException as e:
                    mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Fehler beim Laden der GDT-Datei: " + e.meldung, QMessageBox.StandardButton.Ok)
                    mb.exec()

    def templateMenuLaden(self):
        ladenOk = True
        if self.ungesichertesTemplate:
            mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Beim Laden eines Templates gehen derzeit nicht gesicherte Daten verloren.\nWollen Sie dennoch fortfahren?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            mb.setDefaultButton(QMessageBox.StandardButton.Yes)
            mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
            mb.button(QMessageBox.StandardButton.No).setText("Nein")
            if mb.exec() == QMessageBox.StandardButton.No:
                ladenOk = False
        if ladenOk and self.treeWidgetOriginal.topLevelItemCount() > 0:
            fd = QFileDialog(self)
            fd.setFileMode(QFileDialog.FileMode.ExistingFile)
            fd.setWindowTitle("Template laden")
            fd.setDirectory(self.standardTemplateVerzeichnis)
            fd.setModal(True)
            fd.setViewMode(QFileDialog.ViewMode.Detail)
            fd.setNameFilters(["ogt-Dateien (*.ogt)"])
            fd.setLabelText(QFileDialog.DialogLabel.Accept, "Ok")
            fd.setLabelText(QFileDialog.DialogLabel.Reject, "Abbrechen")
            if fd.exec() == 1:
                templatePfad = fd.selectedFiles()[0]
                try:
                    tree = ElementTree.parse(templatePfad)
                    templateRootElement = tree.getroot()
                    kennfeld = str(templateRootElement.get("kennfeld"))
                    gdtId = str(templateRootElement.get("gdtIdGeraet"))
                    gdtDateiname = str(templateRootElement.get("gdtDateiname"))
                    exportverzeichnis = str(templateRootElement.get("exportverzeichnis"))
                    if os.path.basename(self.gdtDateipfad) == gdtDateiname:
                        self.templateRootElement = templateRootElement
                        exceptions = self.gdtDateiOptimiert.applyTemplate(self.templateRootElement, vorschau=True)
                        self.treeWidgetAusfuellen(self.treeWidgetOptimiert, self.gdtDateiOptimiert)
                        self.labelTreeViewUeberschriftRechts.setText("Optimiert (" + templatePfad + "):")
                        self.setStatusMessage("Template " + templatePfad + " geladen")
                        self.lineEditName.setText(os.path.basename(templatePfad)[:-4])
                        self.lineEditKennfeld.setText(kennfeld)
                        self.checkBoxKennfeld.setChecked(kennfeld != "")
                        self.lineEditGdtId.setText(gdtId)
                        self.checkBoxGdtId.setChecked(gdtId != "")
                        self.lineEditGdtDateiname.setText(gdtDateiname)
                        # self.checkBoxGdtDateiname.setChecked(gdtDateiname != "")
                        self.lineEditExportverzeichnis.setText(exportverzeichnis)
                        self.ungesichertesTemplate = False
                        if len(exceptions) > 0:
                            exceptionListe = "\n-".join(exceptions)
                            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Template-Rückmeldung:\n-" + exceptionListe, QMessageBox.StandardButton.Ok)
                            mb.exec()
                    else:
                        mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Die Template-Datei passt nicht zur geladenen GDT-Datei.", QMessageBox.StandardButton.Ok)
                        mb.exec()
                except:
                        mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Fehler beim Laden des Templates " + templatePfad, QMessageBox.StandardButton.Ok)
                        mb.exec()
        elif ladenOk:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Keine GDT-Datei geladen", QMessageBox.StandardButton.Ok)
            mb.exec()

    def templateMenuSpeichern(self):
        if self.treeWidgetOriginal.topLevelItemCount() > 0:
            formularOk = True
            if self.lineEditName.text().strip() == "":
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Kein Template-Name angegeben", QMessageBox.StandardButton.Ok)
                mb.exec()
                formularOk = False
                self.lineEditName.setFocus()
            if formularOk and self.checkBoxKennfeld.isChecked() and self.lineEditKennfeld.text().strip() != "" and re.match(reKennfeld, self.lineEditKennfeld.text().strip()) == None:
                    mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis", "Das gerätespezifische Kennfeld für das Template sollte aus bis zu vier Buchstaben, gefolgt von zwei Ziffern bestehen.\nSoll es dennoch so übernommen werden (" + self.lineEditKennfeld.text().strip() + ")?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    mb.setDefaultButton(QMessageBox.StandardButton.No)
                    mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                    mb.button(QMessageBox.StandardButton.No).setText("Nein")
                    if mb.exec() == QMessageBox.StandardButton.No:
                        self.lineEditKennfeld.setFocus()
                        self.lineEditKennfeld.selectAll()
                        formularOk = False
            if formularOk and self.checkBoxGdtId.isChecked() and self.lineEditGdtId.text().strip() != "" and re.match(reGdtId, self.lineEditGdtId.text().strip()) == None:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis", "Die GDT-ID für das Template sollte aus acht Zeichen bestehen.\nSoll sie dennoch so übernommen werden (" + self.lineEditGdtId.text().strip() + ")?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.No)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.No:
                    self.lineEditGdtId.setFocus()
                    self.lineEditGdtId.selectAll()
                    formularOk = False
            if formularOk and (self.lineEditGdtDateiname.text().strip() == "" or self.lineEditGdtDateiname.text().strip()[-4:].lower() != ".gdt"):
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis", "Der GDT-Dateiname für das Template ist unzulässig.", QMessageBox.StandardButton.Ok)
                mb.exec()
                self.lineEditGdtDateiname.setFocus()
                self.lineEditGdtDateiname.selectAll()
                formularOk = False
            if formularOk and not os.path.exists(self.lineEditExportverzeichnis.text().strip()):
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis", "Das Exportverzeichnis für das Template existiert nicht.", QMessageBox.StandardButton.Ok)
                mb.exec()
                self.pushButtonExportverzeichnis.setFocus()
                formularOk = False
            if formularOk:
                pfad = os.path.join(self.standardTemplateVerzeichnis, self.lineEditName.text() + ".ogt")
                fd = QFileDialog(self)
                fd.setFileMode(QFileDialog.FileMode.AnyFile)
                fd.setOption(QFileDialog.Option.DontConfirmOverwrite)
                fd.setWindowTitle("Template speichern")
                fd.setDirectory(self.standardTemplateVerzeichnis)
                fd.selectFile(pfad)
                fd.setDefaultSuffix("ogt")
                fd.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
                fd.setModal(True)
                fd.setViewMode(QFileDialog.ViewMode.Detail)
                fd.setNameFilters(["ogt-Dateien (*.ogt)"])
                fd.setLabelText(QFileDialog.DialogLabel.Accept, "Speichern")
                fd.setLabelText(QFileDialog.DialogLabel.Reject, "Abbrechen")
                if fd.exec() == 1:
                    speichernOk = True
                    if os.path.exists(pfad):
                        mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis", "Das Template \"" + self.lineEditName.text().strip() + "\" existiert bereits.\nSoll es überschrieben werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                        mb.setDefaultButton(QMessageBox.StandardButton.No)
                        mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                        mb.button(QMessageBox.StandardButton.No).setText("Nein")
                        if mb.exec() == QMessageBox.StandardButton.No:
                            speichernOk = False
                    if speichernOk:
                        kennfeld = ""
                        if self.checkBoxKennfeld.isChecked():
                            kennfeld = self.lineEditKennfeld.text().strip()
                        self.templateRootElement.set("kennfeld", kennfeld)
                        gdtId = ""
                        if self.checkBoxGdtId.isChecked():
                            gdtId = self.lineEditGdtId.text().strip()
                        self.templateRootElement.set("gdtIdGeraet", gdtId)
                        gdtDateiname = ""
                        # if self.checkBoxGdtDateiname.isChecked():
                        gdtDateiname = self.lineEditGdtDateiname.text().strip()
                        self.templateRootElement.set("gdtDateiname", gdtDateiname)
                        self.templateRootElement.set("exportverzeichnis", self.lineEditExportverzeichnis.text())
                        et = ElementTree.ElementTree(self.templateRootElement)
                        ElementTree.indent(et)
                        try:
                            et.write(fd.selectedFiles()[0], "utf-8", True)
                            self.ungesichertesTemplate = False
                        except Exception as e:
                            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Fehler beim Sepichern des Templates: " + str(e), QMessageBox.StandardButton.Ok)
                            mb.exec()
            elif self.treeWidgetOriginal.topLevelItemCount() == 0:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Keine GDT-Datei geladen", QMessageBox.StandardButton.Ok)
                mb.exec()
        else:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Kein Template definiert. Bitte führen Sie zumindest eine Optimierung durch.", QMessageBox.StandardButton.Ok)
            mb.exec()

    def templateMenuTemplatesVerwalten(self):
        dg = dialogTemplatesVerwalten.TemplatesVerwalten(self.standardTemplateVerzeichnis)
        if dg.exec() == 1:
            # Templates löschen
            for i in range(len(dg.templatenamen)):
                if dg.checkBoxLoeschen[i].isChecked():
                    mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis", "Soll das Template \"" + dg.lineEditName[i].text() + "\" endgültig gelöscht werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    mb.setDefaultButton(QMessageBox.StandardButton.No)
                    mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                    mb.button(QMessageBox.StandardButton.No).setText("Nein")
                    if mb.exec() == QMessageBox.StandardButton.Yes:
                        try:
                            os.unlink(os.path.join(self.standardTemplateVerzeichnis, dg.lineEditName[i].text().strip() + ".ogt"))
                            logger.logger.info("Template " + os.path.join(self.standardTemplateVerzeichnis, dg.lineEditName[i].text().strip() + ".ogt") + " gelöscht")
                        except Exception as e:
                            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis", "Fehler beim Löschen des Templates \"" + os.path.join(self.standardTemplateVerzeichnis, dg.lineEditName[i].text().strip() + ".ogt") + "\": " + str(e), QMessageBox.StandardButton.Ok)
                            mb.exec()
            # Template-Infos ändern
            for i in range(len(dg.templatenamen)):
                tree = ElementTree.parse(os.path.join(self.standardTemplateVerzeichnis, dg.lineEditName[i].text() + ".ogt"))
                rootElement = tree.getroot()
                rootElement.set("kennfeld", dg.lineEditKennfeld[i].text().strip())
                rootElement.set("gdtIdGeraet", dg.lineEditGdtId[i].text().strip())
                rootElement.set("gdtDateiname", dg.lineEditGdtDateiname[i].text().strip())
                rootElement.set("exportverzeichnis", dg.lineEditExportverzeichnis[i].text().strip())
                et = ElementTree.ElementTree(rootElement)
                ElementTree.indent(et)
                try:
                    et.write(os.path.join(self.standardTemplateVerzeichnis, dg.lineEditName[i].text() + ".ogt"), "utf-8", True)
                    logger.logger.info("Info-Attribute von Template " + os.path.join(self.standardTemplateVerzeichnis, dg.lineEditName[i].text() + ".ogt") + " geändert")
                except Exception as e:
                    mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Fehler beim Speichern der Info-Attribute von Template " + os.path.join(self.standardTemplateVerzeichnis, dg.lineEditName[i].text() + ".ogt") + ": " + str(e), QMessageBox.StandardButton.Ok)
                    mb.exec()

    def optimierenMenuZeileHinzufuegen(self, checked, optimierungsId:str=""):
        if self.addOnsFreigeschaltet:
            feldkennung = ""
            inhalt = ""
            # Optimierungselement finden, wenn bereits vorhanden (bearbeiten)
            if optimierungsId != "":
                for optimierungElement in self.templateRootElement.findall("optimierung"):
                    if str(optimierungElement.get("id")) == optimierungsId:
                        feldkennung = str(optimierungElement.find("feldkennung").text) # type:ignore
                        inhalt = str(optimierungElement.find("inhalt").text) # type:ignore
                        break
            if self.treeWidgetOriginal.topLevelItemCount() > 0:
                do = dialogOptimierungAddZeile.OptimierungAddZeile(self.gdtDateiOriginal, feldkennung, inhalt)
                if do.exec() == 1:
                    self.templateRootDefinieren()
                    optimierungElement = class_optimierung.OptiAddZeile(do.lineEditFeldkennung.text(), do.lineEditInhalt.text(), self.templateRootElement)
                    if optimierungsId == "": # Neue zeile
                        self.templateRootElement.append(optimierungElement.getXml())
                    else: # Zeile bearbeiten
                        class_optimierung.Optimierung.replaceOptimierungElement(self.templateRootElement, optimierungsId, optimierungElement.getXml())
                    try:
                        exceptions = self.gdtDateiOptimiert.applyTemplate(self.templateRootElement, vorschau=True)
                        if len(exceptions) == 0:
                            self.setStatusMessage("GDT-Zeile " + class_gdtdatei.GdtDatei.getZeile(do.lineEditFeldkennung.text(), do.lineEditInhalt.text()) + " hinzugefügt")
                        else:
                            exceptionsListe = "\n-".join(exceptions)
                            class_optimierung.Optimierung.removeOptimierungElement(self.templateRootElement, str(optimierungElement.getXml().get("id")))
                            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Die Optimierung wurde nicht gespeichert:\n- " + exceptionsListe + "\nBitte definieren Sie diese neu.", QMessageBox.StandardButton.Ok)
                            mb.exec() 
                        self.treeWidgetAusfuellen(self.treeWidgetOptimiert, self.gdtDateiOptimiert)
                        self.ungesichertesTemplate = True
                    except class_gdtdatei.GdtFehlerException as e:
                        mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Fehler bei der Templateanwendung: " + e.meldung, QMessageBox.StandardButton.Ok)
                        mb.exec()
            else:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Keine GDT-Datei geladen", QMessageBox.StandardButton.Ok)
                mb.exec()
        else:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Für diese Funktion ist eine gültige Lizenz notwendig.", QMessageBox.StandardButton.Ok)
            mb.exec()

    def optimierenMenuZeileAendern(self, checked, optimierungsId:str=""):
        if self.addOnsFreigeschaltet:
            feldkennung = ""
            neuerInhalt = ""
            alleVorkommen = False
            # Optimierungselement finden, wenn bereits vorhanden (bearbeiten)
            if optimierungsId != "":
                for optimierungElement in self.templateRootElement.findall("optimierung"):
                    if str(optimierungElement.get("id")) == optimierungsId:
                        alleVorkommen = optimierungElement.get("alle") == "True"
                        feldkennung = str(optimierungElement.find("feldkennung").text) # type:ignore
                        neuerInhalt = str(optimierungElement.find("inhalt").text) # type:ignore
                        break
            if self.treeWidgetOriginal.topLevelItemCount() > 0:
                do = dialogOptimierungChangeZeile.OptimierungChangeZeile(self.gdtDateiOriginal, alleVorkommen, feldkennung, neuerInhalt)
                if do.exec() == 1:
                    self.templateRootDefinieren()
                    optimierungElement = class_optimierung.OptiChangeZeile(do.comboBoxZeile.currentText()[0:4], do.lineEditNeuerInhalt.text(), do.checkBoxAlle.isChecked(), self.templateRootElement)
                    if optimierungsId == "": # Neue zeile
                        self.templateRootElement.append(optimierungElement.getXml())
                    else: # Zeile bearbeiten
                        class_optimierung.Optimierung.replaceOptimierungElement(self.templateRootElement, optimierungsId, optimierungElement.getXml())
                    try:
                        exceptions = self.gdtDateiOptimiert.applyTemplate(self.templateRootElement, vorschau=True)
                        if len(exceptions) == 0:
                            self.setStatusMessage("GDT-Zeile(n) mit der Feldkennung " + do.comboBoxZeile.currentText()[0:4] + " geändert")
                        else:
                            exceptionsListe = "\n-".join(exceptions)
                            class_optimierung.Optimierung.removeOptimierungElement(self.templateRootElement, str(optimierungElement.getXml().get("id")))
                            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Die Optimierung wurde nicht gespeichert:\n- " + exceptionsListe + "\nBitte definieren Sie diese neu.", QMessageBox.StandardButton.Ok)
                            mb.exec() 
                        self.treeWidgetAusfuellen(self.treeWidgetOptimiert, self.gdtDateiOptimiert)
                        self.ungesichertesTemplate = True
                    except class_gdtdatei.GdtFehlerException as e:
                        mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Fehler bei der Templateanwendung: " + e.meldung, QMessageBox.StandardButton.Ok)
                        mb.exec()
            else:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Keine GDT-Datei geladen", QMessageBox.StandardButton.Ok)
                mb.exec()
        else:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Für diese Funktion ist eine gültige Lizenz notwendig.", QMessageBox.StandardButton.Ok)
            mb.exec()

    def optimierenMenuZeileEntfernen(self, checked, optimierungsId:str=""):
        if self.addOnsFreigeschaltet:
            feldkennung = ""
            alleVorkommen = False
            # Optimierungselement finden, wenn bereits vorhanden (bearbeiten)
            if optimierungsId != "":
                for optimierungElement in self.templateRootElement.findall("optimierung"):
                    if str(optimierungElement.get("id")) == optimierungsId:
                        alleVorkommen = optimierungElement.get("alle") == "True"
                        feldkennung = str(optimierungElement.find("feldkennung").text) # type:ignore
                        break
            if self.treeWidgetOriginal.topLevelItemCount() > 0:
                do = dialogOptimierungDeleteZeile.OptimierungDeleteZeile(alleVorkommen, feldkennung)
                if do.exec() == 1:
                    self.templateRootDefinieren()
                    optimierungElement = class_optimierung.OptiDeleteZeile(do.lineEditFeldkennung.text(), do.checkBoxAlle.isChecked(), self.templateRootElement)
                    if optimierungsId == "": # Neue zeile
                        self.templateRootElement.append(optimierungElement.getXml())
                    else: # Zeile bearbeiten
                        class_optimierung.Optimierung.replaceOptimierungElement(self.templateRootElement, optimierungsId, optimierungElement.getXml())
                    try:
                        exceptions = self.gdtDateiOptimiert.applyTemplate(self.templateRootElement, vorschau=True)
                        if len(exceptions) == 0:
                            self.setStatusMessage("GDT-Zeile(n) mit der Feldkennung " + do.lineEditFeldkennung.text() + " entfernt")
                        else:
                            exceptionsListe = "\n-".join(exceptions)
                            class_optimierung.Optimierung.removeOptimierungElement(self.templateRootElement, str(optimierungElement.getXml().get("id")))
                            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Die Optimierung wurde nicht gespeichert:\n- " + exceptionsListe + "\nBitte definieren Sie diese neu.", QMessageBox.StandardButton.Ok)
                            mb.exec() 
                        self.treeWidgetAusfuellen(self.treeWidgetOptimiert, self.gdtDateiOptimiert)
                        self.ungesichertesTemplate = True
                    except class_gdtdatei.GdtFehlerException as e:
                        mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Fehler bei der Templateanwendung: " + e.meldung, QMessageBox.StandardButton.Ok)
                        mb.exec()
            else:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Keine GDT-Datei geladen", QMessageBox.StandardButton.Ok)
                mb.exec()
        else:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Für diese Funktion ist eine gültige Lizenz notwendig.", QMessageBox.StandardButton.Ok)
            mb.exec()

    def optimierenMenuTestAendern(self, checked, optimierungsId:str=""):
        if self.addOnsFreigeschaltet:
            eindeutigkeitskriterien = {}
            aenderungen = {}
            # Optimierungselement finden, wenn bereits vorhanden (bearbeiten)
            if optimierungsId != "":
                for optimierungElement in self.templateRootElement.findall("optimierung"):
                    if str(optimierungElement.get("id")) == optimierungsId:
                        eindeutigkeitskriterienElement = optimierungElement.find("eindeutigkeitskriterien")
                        for kriteriumElement in eindeutigkeitskriterienElement.findall("kriterium"): # type: ignore
                            feldkennung = str(kriteriumElement.get("feldkennung"))
                            inhalt = kriteriumElement.text
                            eindeutigkeitskriterien[feldkennung] = inhalt
                        for aenderungElement in optimierungElement.findall("aenderung"):
                            feldkennung = str(aenderungElement.get("feldkennung"))
                            inhalt = aenderungElement.text
                            aenderungen[feldkennung] = inhalt
                        break
            if self.treeWidgetOriginal.topLevelItemCount() > 0:
                do = dialogOptimierungChangeTest.OptimierungChangeTest(self.gdtDateiOriginal, self.maxeindeutigkeitskriterien, self.maxtestaenderungen, eindeutigkeitskriterien, aenderungen)
                if do.exec() == 1:
                    exceptions = []
                    self.templateRootDefinieren()
                    optimierungElement = class_optimierung.OptiChangeTest(do.eindeutigkeitskriterien, do.aenderungen, self.templateRootElement)
                    if optimierungsId == "": # Neue zeile
                        self.templateRootElement.append(optimierungElement.getXml())
                    else: # Zeile bearbeiten
                        class_optimierung.Optimierung.replaceOptimierungElement(self.templateRootElement, optimierungsId, optimierungElement.getXml())
                    try:
                        exceptions = self.gdtDateiOptimiert.applyTemplate(self.templateRootElement, vorschau=True)
                        if len(exceptions) == 0:
                            self.setStatusMessage("Test geändert")
                        else:
                            exceptionsListe = "\n-".join(exceptions)
                            class_optimierung.Optimierung.removeOptimierungElement(self.templateRootElement, str(optimierungElement.getXml().get("id")))
                            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Die Optimierung wurde nicht gespeichert:\n- " + exceptionsListe + "\nBitte definieren Sie diese neu.", QMessageBox.StandardButton.Ok)
                            mb.exec() 
                        self.treeWidgetAusfuellen(self.treeWidgetOptimiert, self.gdtDateiOptimiert)
                        self.ungesichertesTemplate = True
                    except class_gdtdatei.GdtFehlerException as e:
                        mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Fehler bei der Templateanwendung: " + e.meldung, QMessageBox.StandardButton.Ok)
                        mb.exec()
            else:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Keine GDT-Datei geladen", QMessageBox.StandardButton.Ok)
                mb.exec()
        else:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Für diese Funktion ist eine gültige Lizenz notwendig.", QMessageBox.StandardButton.Ok)
            mb.exec()

    def optimierenMenuTestEntfernen(self, checked, optimierungsId:str=""):
        if self.addOnsFreigeschaltet:
            eindeutigkeitskriterien = {}
            # Optimierungselement finden, wenn bereits vorhanden (bearbeiten)
            if optimierungsId != "":
                for optimierungElement in self.templateRootElement.findall("optimierung"):
                    if str(optimierungElement.get("id")) == optimierungsId:
                        eindeutigkeitskriterienElement = optimierungElement.find("eindeutigkeitskriterien")
                        for kriteriumElement in eindeutigkeitskriterienElement.findall("kriterium"): # type: ignore
                            feldkennung = str(kriteriumElement.get("feldkennung"))
                            inhalt = kriteriumElement.text
                            eindeutigkeitskriterien[feldkennung] = inhalt
                        break
            if self.treeWidgetOriginal.topLevelItemCount() > 0:
                do = dialogOptimierungDeleteTest.OptimierungDeleteTest(self.gdtDateiOriginal, self.maxeindeutigkeitskriterien, eindeutigkeitskriterien)
                if do.exec() == 1:
                    exceptions = []
                    self.templateRootDefinieren()
                    optimierungElement = class_optimierung.OptiDeleteTest(do.eindeutigkeitskriterien, self.templateRootElement)
                    if optimierungsId == "": # Neue zeile
                        self.templateRootElement.append(optimierungElement.getXml())
                    else: # Zeile bearbeiten
                        class_optimierung.Optimierung.replaceOptimierungElement(self.templateRootElement, optimierungsId, optimierungElement.getXml())
                    try:
                        exceptions = self.gdtDateiOptimiert.applyTemplate(self.templateRootElement, vorschau=True)
                        if len(exceptions) == 0:
                            self.setStatusMessage("Test entfernt")
                        else:
                            exceptionsListe = "\n-".join(exceptions)
                            class_optimierung.Optimierung.removeOptimierungElement(self.templateRootElement, str(optimierungElement.getXml().get("id")))
                            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Die Optimierung wurde nicht gespeichert:\n- " + exceptionsListe + "\nBitte definieren Sie diese neu.", QMessageBox.StandardButton.Ok)
                            mb.exec() 
                        self.treeWidgetAusfuellen(self.treeWidgetOptimiert, self.gdtDateiOptimiert)
                        self.ungesichertesTemplate = True
                    except class_gdtdatei.GdtFehlerException as e:
                        mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Fehler bei der Templateanwendung: " + e.meldung, QMessageBox.StandardButton.Ok)
                        mb.exec()
            else:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Keine GDT-Datei geladen", QMessageBox.StandardButton.Ok)
                mb.exec()
        else:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Für diese Funktion ist eine gültige Lizenz notwendig.", QMessageBox.StandardButton.Ok)
            mb.exec()

    def optimierenMenuTestAus6228(self, checked, optimierungsId:str=""):
        if self.addOnsFreigeschaltet:
            trennRegexPattern = ""
            erkennungstext = ""
            erkennungsspalte = 0
            ergebnisspalte = 0
            testIdent = ""
            testBezeichnung = ""
            testEinheit = ""
            # Optimierungselement finden, wenn bereits vorhanden (bearbeiten)
            if optimierungsId != "":
                for optimierungElement in self.templateRootElement.findall("optimierung"):
                    if str(optimierungElement.get("id")) == optimierungsId:
                        trennRegexPattern = str(optimierungElement.find("trennRegexPattern").text) # type:ignore
                        erkennungstext = str(optimierungElement.find("erkennungstext").text) # type:ignore
                        erkennungsspalte = int(optimierungElement.find("erkennungsspalte").text) # type:ignore
                        ergebnisspalte = int(optimierungElement.find("ergebnisspalte").text) # type:ignore
                        testIdent = str(optimierungElement.find("testIdent").text) # type:ignore
                        testBezeichnung = str(optimierungElement.find("testBezeichnung").text) # type:ignore
                        testEinheit = str(optimierungElement.find("testEinheit").text) # type:ignore
                        break
            if self.treeWidgetOriginal.topLevelItemCount() > 0:
                if len(self.gdtDateiOriginal.getInhalte("6228")) > 0:
                    do = dialogOptimierungTestAus6228.OptimierungTestAus6228(self.gdtDateiOriginal, trennRegexPattern, erkennungstext, erkennungsspalte, ergebnisspalte, testIdent, testBezeichnung, testEinheit, self.standard6228trennregexpattern, self.maxAnzahl6228Spalten)
                    if do.exec() == 1:
                        self.templateRootDefinieren()
                        optimierungElement = class_optimierung.OptiTestAus6228(do.lineEditTrennRegexPattern.text(), do.lineEditErkennungstext.text(), int(do.lineEditErkennungsspalte.text()), int(do.lineEditErgebnisspalte.text()), do.lineEditTestIdent.text(), do.lineEditTestBezeichnung.text(), do.lineEditTestEinheit.text(), self.templateRootElement)
                        if optimierungsId == "": # Neue zeile
                            self.templateRootElement.append(optimierungElement.getXml())
                        else: # Zeile bearbeiten
                            class_optimierung.Optimierung.replaceOptimierungElement(self.templateRootElement, optimierungsId, optimierungElement.getXml())
                        try:
                            exceptions = self.gdtDateiOptimiert.applyTemplate(self.templateRootElement, vorschau=True)
                            if len(exceptions) == 0:
                                self.setStatusMessage("Test geändert")
                            else:
                                exceptionsListe = "\n-".join(exceptions)
                                class_optimierung.Optimierung.removeOptimierungElement(self.templateRootElement, str(optimierungElement.getXml().get("id")))
                                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Die Optimierung wurde nicht gespeichert:\n- " + exceptionsListe + "\nBitte definieren Sie diese neu.", QMessageBox.StandardButton.Ok)
                                mb.exec() 
                            self.treeWidgetAusfuellen(self.treeWidgetOptimiert, self.gdtDateiOptimiert)
                            self.ungesichertesTemplate = True
                        except class_gdtdatei.GdtFehlerException as e:
                            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Fehler bei der Templateanwendung: " + e.meldung, QMessageBox.StandardButton.Ok)
                            mb.exec()
                else:
                    mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Die geladene GDT-Datei enthält keine 6228-Zeilen.", QMessageBox.StandardButton.Ok)
                    mb.exec()
            else:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Keine GDT-Datei geladen", QMessageBox.StandardButton.Ok)
                mb.exec()
        else:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Für diese Funktion ist eine gültige Lizenz notwendig.", QMessageBox.StandardButton.Ok)
            mb.exec()

    def optimierenMenuBefundAusTest(self, checked, optimierungsId:str=""):
        if self.addOnsFreigeschaltet:
            testuebernahmen = [dialogOptimierungBefundAusTest.Testuebernahme("", "", {})]
            befundzeile = ""
            # Optimierungselement finden, wenn bereits vorhanden (bearbeiten)
            if optimierungsId != "":
                for optimierungElement in self.templateRootElement.findall("optimierung"):
                    if str(optimierungElement.get("id")) == optimierungsId:
                        eindeutigkeitskriterien = {}
                        for testElement in optimierungElement.findall("test"):
                            eindeutigkeitskriterienElement = testElement.find("eindeutigkeitskriterien")
                            variableElement = testElement.find("variable")
                            for kriterium in eindeutigkeitskriterienElement.findall("kriterium"): # type: ignore
                                feldkennung = str(kriterium.get("feldkennung"))
                                kriterium = str(kriterium.text)
                                eindeutigkeitskriterien[feldkennung] = kriterium
                            platzhalterFeldkennung = str(variableElement.find("feldkennung").text) # type: ignore
                            platzhalterName = str(variableElement.find("name").text) # type: ignore
                            testuebernahme = dialogOptimierungBefundAusTest.Testuebernahme(platzhalterName, platzhalterFeldkennung, eindeutigkeitskriterien)
                            testuebernahmen.append(testuebernahme)
                        befundElement = optimierungElement.find("befund")
                        befundzeile = str(befundElement.text) # type: ignore
                        break
            if self.treeWidgetOriginal.topLevelItemCount() > 0:
                do = dialogOptimierungBefundAusTest.OptimierungBefundAusTest(self.gdtDateiOriginal, self.maxeindeutigkeitskriterien, testuebernahmen, befundzeile)
                if do.exec() == 1:
                    self.templateRootDefinieren()
                    optimierungElement = class_optimierung.OptiBefundAusTest(do.testuebernahmen, do.lineEditBefundzeile.text(), self.templateRootElement)
                    if optimierungsId == "": # Neue zeile
                        self.templateRootElement.append(optimierungElement.getXml())
                    else: # Zeile bearbeiten
                        class_optimierung.Optimierung.replaceOptimierungElement(self.templateRootElement, optimierungsId, optimierungElement.getXml())
                    try:
                        exceptions = self.gdtDateiOptimiert.applyTemplate(self.templateRootElement, vorschau=True)
                        if len(exceptions) == 0:
                            self.setStatusMessage("Befundzeile erzeugt")
                        else:
                            exceptionsListe = "\n-".join(exceptions)
                            class_optimierung.Optimierung.removeOptimierungElement(self.templateRootElement, str(optimierungElement.getXml().get("id")))
                            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Die Optimierung wurde nicht gespeichert:\n- " + exceptionsListe + "\nBitte definieren Sie diese neu.", QMessageBox.StandardButton.Ok)
                            mb.exec() 
                        self.treeWidgetAusfuellen(self.treeWidgetOptimiert, self.gdtDateiOptimiert)
                        self.ungesichertesTemplate = True
                    except class_gdtdatei.GdtFehlerException as e:
                        mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Fehler bei der Templateanwendung: " + e.meldung, QMessageBox.StandardButton.Ok)
                        mb.exec()
            else:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Keine GDT-Datei geladen", QMessageBox.StandardButton.Ok)
                mb.exec()
        else:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Für diese Funktion ist eine gültige Lizenz notwendig.", QMessageBox.StandardButton.Ok)
            mb.exec()

    def optimierenMenuInhalteZusammenfuehren(self, checked, optimierungsId:str=""):
        if self.addOnsFreigeschaltet:
            feldkennung = ""
            # Optimierungselement finden, wenn bereits vorhanden (bearbeiten)
            if optimierungsId != "":
                for optimierungElement in self.templateRootElement.findall("optimierung"):
                    if str(optimierungElement.get("id")) == optimierungsId:
                        feldkennung = str(optimierungElement.find("feldkennung").text) # type:ignore
                        break
            if self.treeWidgetOriginal.topLevelItemCount() > 0:
                do = dialogOptimierungConcatInhalte.OptimierungConcatInhalte(feldkennung)
                if do.exec() == 1:
                    self.templateRootDefinieren()
                    optimierungElement = class_optimierung.OptiConcatInhalte(do.lineEditFeldkennung.text(), self.templateRootElement)
                    if optimierungsId == "": # Neue zeile
                        self.templateRootElement.append(optimierungElement.getXml())
                    else: # Zeile bearbeiten
                        class_optimierung.Optimierung.replaceOptimierungElement(self.templateRootElement, optimierungsId, optimierungElement.getXml())
                    try:
                        exceptions = self.gdtDateiOptimiert.applyTemplate(self.templateRootElement, vorschau=True)
                        if len(exceptions) == 0:
                            self.setStatusMessage("Inhalte der GDT-Zeilen mit der Feldkennung " + do.lineEditFeldkennung.text() + " zusammengeführt")
                        else:
                            exceptionsListe = "\n-".join(exceptions)
                            class_optimierung.Optimierung.removeOptimierungElement(self.templateRootElement, str(optimierungElement.getXml().get("id")))
                            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Die Optimierung wurde nicht gespeichert:\n- " + exceptionsListe + "\nBitte definieren Sie diese neu.", QMessageBox.StandardButton.Ok)
                            mb.exec() 
                        self.treeWidgetAusfuellen(self.treeWidgetOptimiert, self.gdtDateiOptimiert)
                        self.ungesichertesTemplate = True
                    except class_gdtdatei.GdtFehlerException as e:
                        mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Fehler bei der Templateanwendung: " + e.meldung, QMessageBox.StandardButton.Ok)
                        mb.exec()
            else:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Keine GDT-Datei geladen", QMessageBox.StandardButton.Ok)
                mb.exec()
        else:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Für diese Funktion ist eine gültige Lizenz notwendig.", QMessageBox.StandardButton.Ok)
            mb.exec()
                
    def templateRootDefinieren(self):
        if self.templateRootElement.get("exportverzeichnis") == "":
            self.templateRootElement.set("kennfeld", self.lineEditKennfeld.text().strip())
            self.templateRootElement.set("gdtIdGeraet", self.lineEditGdtId.text().strip())
            self.templateRootElement.set("gdtDateiname", self.lineEditGdtDateiname.text().strip())
            self.templateRootElement.set("exportverzeichnis", self.lineEditExportverzeichnis.text())

    def optimierungBearbeiten(self):
        try:
            optimierungsId = self.optimierungsIds[self.treeWidgetOptimiert.currentItem().text(0).strip()]
            optimierungstyp = class_optimierung.Optimierung.getTypVonId(self.templateRootElement, optimierungsId)
            if optimierungstyp == "addZeile":
                self.optimierenMenuZeileHinzufuegen(False, optimierungsId)
            elif optimierungstyp == "changeZeile":
                self.optimierenMenuZeileAendern(False, optimierungsId)
            elif optimierungstyp == "deleteZeile":
                self.optimierenMenuZeileEntfernen(False, optimierungsId)
            elif optimierungstyp == "changeTest":
                self.optimierenMenuTestAendern(False, optimierungsId)
            elif optimierungstyp == "deleteTest":
                self.optimierenMenuTestEntfernen(False, optimierungsId)
            elif optimierungstyp == "testAus6228":
                self.optimierenMenuTestAus6228(False, optimierungsId)
            elif optimierungstyp == "befundAusTest":
                self.optimierenMenuBefundAusTest(False, optimierungsId)
            elif optimierungstyp == "concatInhalte":
                self.optimierenMenuInhalteZusammenfuehren(False, optimierungsId)
            self.setStatusMessage("Optimierung bearbeitet")
        except class_gdtdatei.GdtFehlerException as e:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Fehler beim Bebrbeiten der Optimierung: " + e.meldung, QMessageBox.StandardButton.Ok)
            mb.exec()

    def optimierungEntfernen(self):
        optimierungsId = self.optimierungsIds[self.treeWidgetOptimiert.currentItem().text(0).strip()]
        mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Soll die ausgewählte Optimierung wirklich entfernt werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        mb.setDefaultButton(QMessageBox.StandardButton.Yes)
        mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
        mb.button(QMessageBox.StandardButton.No).setText("Nein")
        if mb.exec() == QMessageBox.StandardButton.Yes:
            try:
                class_optimierung.Optimierung.removeOptimierungElement(self.templateRootElement, optimierungsId)
                self.gdtDateiOptimiert.applyTemplate(self.templateRootElement, vorschau=True)
                self.treeWidgetAusfuellen(self.treeWidgetOptimiert, self.gdtDateiOptimiert)
                self.setStatusMessage("Optimierung entfernt")
            except class_gdtdatei.GdtFehlerException as e:
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Fehler beim Entfernen der Optimierung: " + e.meldung, QMessageBox.StandardButton.Ok)
                mb.exec()

    def pushButtonUeberwachungStartenClicked(self, checked):
        if checked:
            if os.path.exists(self.gdtImportVerzeichnis):
                # Importverzeichnis auf nicht bearbeitete GDT-Dateien prüfen
                gdtDateien = []
                for importordnerFile in os.listdir(self.gdtImportVerzeichnis):
                    if importordnerFile[-4:].lower() == ".gdt":
                        gdtDateien.append(importordnerFile)
                if len(gdtDateien) > 0:
                    mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Es sind noch nicht bearbeitete GDT-Dateien im Importverzeichnis. Sollen diese jetzt bearbeitet werden?\nDurch Klick auf \"Nein\" werden die Dateien gelöscht.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                    mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                    mb.button(QMessageBox.StandardButton.No).setText("Nein")
                    if mb.exec() == QMessageBox.StandardButton.Yes:
                        self.directoryChanged()
                    else:
                        for gdtDatei in gdtDateien:
                            os.unlink(os.path.join(self.gdtImportVerzeichnis, gdtDatei))
                self.tray.showMessage("OptiGDT", "Überwachung gestartet")
                self.tray.setToolTip("OptiGDT-Überwachung aktiv")
                logger.logger.info("FileSystemWatcher instanziert")
                fsw.addPath(self.gdtImportVerzeichnis)
                logger.logger.info("Importverzeichnis " + self.gdtImportVerzeichnis + " dem Watcher hinzugefügt")
                fsw.directoryChanged.connect(self.directoryChanged) # type: ignore
                logger.logger.info("Methode directoryChanged verbunden")
                self.pushButtonUeberwachungStarten.setText("Verzeichnisüberwachung anhalten")
                self.pushButtonUeberwachungStarten.setStyleSheet("background:rgb(50,150,50);color:rgb(255,255,255);border:2px solid rgb(0,0,0)")
                self.setStatusMessage("Verzeichnisüberwachung gestartet")
                self.trayMenuZeigenAction.setEnabled(True)
                self.ueberwachungAktiv = True
                if not self.isHidden():
                    self.setWindowState(Qt.WindowState.WindowNoState)
                    self.setHidden(True)
            else:
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Das Importverzeichnis \"" + self.gdtImportVerzeichnis + "\" existiert nicht.", QMessageBox.StandardButton.Ok)
                mb.exec()
        else:
            self.pushButtonUeberwachungStarten.setStyleSheet("background:rgb(0,50,0);color:rgb(255,255,255);border:2px solid rgb(0,0,0)")
            self.pushButtonUeberwachungStarten.setText("Verzeichnisüberwachung starten")
            fsw.removePath(self.gdtImportVerzeichnis)
            logger.logger.info("Importverzeichnis " + self.gdtImportVerzeichnis + " vom Watcher entfernt")
            self.tray.showMessage("OptiGDT", "Überwachung angehalten")
            self.setStatusMessage("Verzeichnisüberwachung angehalten")
            self.tray.setToolTip("OptiGDT-Überwachung inaktiv")
            self.ueberwachungAktiv = False
            
    def deleteImportverzeichnis(self):
        for file in os.listdir(self.gdtImportVerzeichnis):
            os.unlink(file)

    def directoryChanged(self):
        """
        Durchsucht das Verzeichnis nach .gdt-Dateien, wendet das entsprechrende Template an, speichert die Datei im Exportverzeichnis unter dem gleichen Namen und löscht die importierte Datei
        """
        time.sleep(self.sekundenBisTemplatebearbeitung)
        logger.logger.info("Innerhalb directoryChanged")
        files = os.listdir(self.gdtImportVerzeichnis)
        for gdtDateiname in files:
            logger.logger.info("Name in files: " + gdtDateiname)
            if len(gdtDateiname) > 4:
                dateiendung = gdtDateiname[-4:]
                if dateiendung.lower() == ".gdt":
                    logger.logger.info("GDT-Datei " + gdtDateiname + " gefunden")
                    gd = class_gdtdatei.GdtDatei(class_gdtdatei.GdtZeichensatz.IBM_CP437)
                    gd.laden(os.path.join(self.gdtImportVerzeichnis, gdtDateiname))
                    logger.logger.info("GDT-Datei " + gdtDateiname + " geladen")
                    # Zeichensatz der geladenen GDT-Datei prüfen und ggf. anpassen
                    zeichensatz = 2
                    try:
                        zeichensatz = int(gd.getInhalte("9206")[0])
                    except:
                        pass
                    if zeichensatz != 2:
                        gd.setZeichensatz(class_gdtdatei.GdtZeichensatz(zeichensatz))
                        logger.logger.info("Zeichensatz auf " + str(class_gdtdatei.GdtZeichensatz(zeichensatz)) + " geändert")
                        gd.laden(os.path.join(self.gdtImportVerzeichnis, gdtDateiname))
                        logger.logger.info("GDT-Datei " + os.path.join(self.gdtImportVerzeichnis, gdtDateiname) + " mit Zeichensatz " + str(class_gdtdatei.GdtZeichensatz(zeichensatz)) + " geladen")
                    # Gerätespez. Kennfeld und GDT-ID prüfen
                    kennfeldGdtDatei = ""
                    try:
                        kennfeldGdtDatei = str(gd.getInhalte("8402")[0])
                    except:
                        pass
                    gdtIdGdtDatei = ""
                    try:
                        gdtIdGdtDatei = str(gd.getInhalte("8316")[0])
                    except:
                        pass
                    files = os.listdir(self.standardTemplateVerzeichnis)
                    templateGefunden = False
                    for templateDateiname in files:
                        if templateDateiname[-4:] == ".ogt":
                            kennfeldTemplate = class_gdtdatei.GdtDatei.getTemplateInfo(os.path.join(self.standardTemplateVerzeichnis, templateDateiname))[0]
                            gdtIdTemplate = class_gdtdatei.GdtDatei.getTemplateInfo(os.path.join(self.standardTemplateVerzeichnis, templateDateiname))[1]
                            gdtDateinameInTemplate = class_gdtdatei.GdtDatei.getTemplateInfo(os.path.join(self.standardTemplateVerzeichnis, templateDateiname))[2]
                            exportverzeichnis = class_gdtdatei.GdtDatei.getTemplateInfo(os.path.join(self.standardTemplateVerzeichnis, templateDateiname))[3]
                            kennfeldKorrekt = True
                            if kennfeldTemplate != "":
                                kennfeldKorrekt = kennfeldGdtDatei == kennfeldTemplate
                            gdtIdKorrekt = True
                            if gdtIdTemplate != "":
                                gdtIdKorrekt = gdtIdGdtDatei == gdtIdTemplate
                            logger.logger.info("Vorhandenes Template: " + os.path.join(self.standardTemplateVerzeichnis, templateDateiname))
                            if gdtDateinameInTemplate == gdtDateiname and kennfeldKorrekt and gdtIdKorrekt:
                                templateGefunden = True
                                logger.logger.info("Zu " + gdtDateiname + " passendendes Template " + os.path.join(self.standardTemplateVerzeichnis, templateDateiname) + " gefunden")
                                try:
                                    exceptions = gd.applyTemplateVonPfad(os.path.join(self.standardTemplateVerzeichnis, templateDateiname))
                                    logger.logger.info(os.path.join(self.standardTemplateVerzeichnis, templateDateiname) + " angewendet")
                                    if len(exceptions) > 0:
                                        exceptionListe = ", ".join(exceptions)
                                        logger.logger.warning("Fehlerliste nach Templateanwendung: " + exceptionListe)
                                    gd.setSatzlaenge()
                                    with open(os.path.join(exportverzeichnis, gdtDateiname), "w", encoding=gd.getZeichensatzAlsPythonString(), newline="\r\n") as file:
                                        for zeile in gd.getZeilen():
                                            file.write(zeile + "\r\n")
                                    logger.logger.info("Optimierte GDT-Datei " + gdtDateiname + " gespeichert") 
                                    os.unlink(os.path.join(self.gdtImportVerzeichnis, gdtDateiname))
                                    logger.logger.info("Originale GDT-Datei " + gdtDateiname + " gelöscht")
                                    break
                                except class_optimierung.OptimierungsfehlerException as e:
                                    logger.logger.warning("Exception in class_filesystemwatcher bei Templateanwendung: " + e.meldung)
                    if not templateGefunden:
                        logger.logger.warning("Template für GDT-Datei " + gdtDateiname + " nicht gefunden")
                        raise class_optimierung.OptimierungsfehlerException("Template für GDT-Datei " + gdtDateiname + " nicht gefunden")
            else:
                logger.logger.info("Dateiname zu kurz: " + gdtDateiname)   

    def trayMenuZeigen(self):
        self.showNormal()
        self.trayMenuZeigenAction.setEnabled(False)

    def trayMenuBeenden(self):
        if self.ueberwachungAktiv:
            mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "trayDie GDT-Verzeichnisübrewachung ist aktiv.\nSoll OptiGDT dennoch beendet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, self)
            mb.setDefaultButton(QMessageBox.StandardButton.No)
            mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
            mb.button(QMessageBox.StandardButton.No).setText("Nein")
            if mb.exec() == QMessageBox.StandardButton.Yes:
                sys.exit()
        else:
            sys.exit()
    
    # Statische Methoden
    @staticmethod
    def setTreeWidgetZeileSchriftfarbe(treeWidget:QTreeWidget, index:int, r:int, g:int, b:int):
            for i in range(treeWidget.columnCount()):
                treeWidget.topLevelItem(index).setForeground(i, QColor(r, g, b))

    @staticmethod
    def setTreeWidgetZeileHintergrund(treeWidget:QTreeWidget, index:int, farbe:QColor):
        for i in range(treeWidget.columnCount()):
            treeWidget.topLevelItem(index).setBackground(i, farbe)

    @staticmethod
    def setTreeWidgetItemHintergrund(item:QTreeWidgetItem, anzahlColumns:int, farbe:QColor):
        for i in range(anzahlColumns):
            item.setBackground(i, farbe)
            
app = QApplication(sys.argv)
fsw = QFileSystemWatcher(app)
qt = QTranslator()
filename = "qtbase_de"
directory = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
qt.load(filename, directory)
app.installTranslator(qt)
app.setWindowIcon(QIcon(os.path.join(basedir, "icons/program.png")))
window = MainWindow()
if not "bg" in sys.argv:
    window.show()
app.exec()