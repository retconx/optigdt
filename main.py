import sys, configparser, os, datetime, shutil, logger, re, time, atexit, subprocess
import class_gdtdatei, class_optimierung, class_importWorker, class_Enums, farbe
## Nur mit Lizenz
import gdttoolsL
## /Nur mit Lizenz
import xml.etree.ElementTree as ElementTree
import dialogUeberOptiGdt, dialogEinstellungenGdt, dialogEinstellungenOptimierung, dialogEinstellungenLanrLizenzschluessel, dialogOptimierungAddZeile, dialogOptimierungDeleteZeile, dialogOptimierungChangeTest, dialogOptimierungTestAus6228, dialogOptimierungBefundAusTest, dialogOptimierungConcatInhalte, dialogOptimierungDeleteTest, dialogTemplatesVerwalten, dialogOptimierungChangeZeile, dialogEula, dialogOptimierungAddPdf, dialogEinstellungenImportExport, dialogEinstellungenAllgemein
from PySide6.QtCore import Qt, QTranslator, QLibraryInfo, QFileSystemWatcher, QThreadPool
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
reGdtDateiendungSequentiell = r"^\.\d{3}$"
reGdtDateiendung = r"^\.gdt|\.\d{3}$"

# Farbdefinitionen (bis 2.12.0)
#testauswahlHintergrund = QColor(220,220,220)
#concatHintergrund = QColor(255,220,255)
#addZeileHintergrund =  QColor(220,255,220)
# changeZeileHintergrund = QColor(255,220,220)
# changeTestHintergrund = QColor(220,220,255)
# testAus6228Hintergrund = QColor(255,255,220)
# befundAusTestHintergrund = QColor(220,255,255)

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
            mb.setDefaultButton(QMessageBox.StandardButton.No)
            mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
            mb.button(QMessageBox.StandardButton.No).setText("Nein")
            if mb.exec() == QMessageBox.StandardButton.No:
                e.ignore()
        if self.ueberwachungAktiv:
            mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Die GDT-Verzeichnisübrewachung ist aktiv.\nSoll OptiGDT dennoch beendet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            mb.setDefaultButton(QMessageBox.StandardButton.No)
            mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
            mb.button(QMessageBox.StandardButton.No).setText("Nein")
            if mb.exec() == QMessageBox.StandardButton.No:
                e.ignore()
        self.tray.hide()

    def showEvent(self, e):
        self.activateWindow()

    def __init__(self):
        super().__init__()
        self.threadPool = QThreadPool()
        self.importWorker = None
        self.tray = QSystemTrayIcon(app)
        icon = QIcon(os.path.join(basedir, "icons/program.png"))
        self.tray.setIcon(icon)
        self.tray.setToolTip("OptiGDT-Überwachung inaktiv")
        self.trayMenu = QMenu()
        self.trayMenuZeigenAction = QAction("OptiGDT zeigen", self)
        self.trayMenuZeigenAction.setEnabled(False)
        self.trayMenuUeberwachungNeuStartenAction = QAction("Verzeichnisüberwachung neu starten")
        self.trayMenuUeberwachungNeuStartenAction.setEnabled(False)
        self.trayMenuBeendenAction = QAction("OptiGDT beenden", self)
        self.trayMenu.addAction(self.trayMenuZeigenAction)
        self.trayMenu.addAction(self.trayMenuUeberwachungNeuStartenAction)
        self.trayMenu.addAction(self.trayMenuBeendenAction)
        self.trayMenuZeigenAction.triggered.connect(self.trayMenuZeigen) 
        self.trayMenuUeberwachungNeuStartenAction.triggered.connect(self.trayMenuUeberwachungNeuStarten)
        self.trayMenuBeendenAction.triggered.connect(self.trayMenuBeenden) 
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
        # 2.0.8
        self.eulagelesen = False
        if self.configIni.has_option("Allgemein", "eulagelesen"):
            self.eulagelesen = self.configIni["Allgemein"]["eulagelesen"] == "True"
        # 2.2.0
        self.punktinkomma6220 = False
        if self.configIni.has_option("Optimierung", "punktinkomma6220"):
            self.punktinkomma6220 = self.configIni["Optimierung"]["punktinkomma6220"] == "True"
        # 2.3.0
        self.autoupdate = True
        if self.configIni.has_option("Allgemein", "autoupdate"):
            self.autoupdate = self.configIni["Allgemein"]["autoupdate"] == "True"
        # 2.7.0
        self.gdtImportVerzeichnisSekundaer = ""
        if self.configIni.has_option("GDT", "gdtimportverzeichnissekundaer"):
            self.gdtImportVerzeichnisSekundaer = self.configIni["GDT"]["gdtimportverzeichnissekundaer"]
        # 2.7.5
        self.sekundaeresimportverzeichnispruefen = False
        if self.configIni.has_option("Optimierung", "sekundaeresimportverzeichnispruefen"):
            self.sekundaeresimportverzeichnispruefen = self.configIni["Optimierung"]["sekundaeresimportverzeichnispruefen"] == "True"
        # 2.9.0
        self.updaterpfad = ""
        if self.configIni.has_option("Allgemein", "updaterpfad"):
            self.updaterpfad = self.configIni["Allgemein"]["updaterpfad"]
        # /Nachträglich hinzufefügte Options

        ## Nur mit Lizenz
        # Prüfen, ob Lizenzschlüssel unverschlüsselt
        if len(self.lizenzschluessel) == 29:
            logger.logger.info("Lizenzschlüssel unverschlüsselt")
            self.configIni["Erweiterungen"]["lizenzschluessel"] = gdttoolsL.GdtToolsLizenzschluessel.krypt(self.lizenzschluessel)
            with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                    self.configIni.write(configfile)
        else:
            self.lizenzschluessel = gdttoolsL.GdtToolsLizenzschluessel.dekrypt(self.lizenzschluessel)
        ## /Nur mit Lizenz

        # Prüfen, ob EULA gelesen
        if not self.eulagelesen:
            de = dialogEula.Eula()
            de.exec()
            if de.checkBoxZustimmung.isChecked():
                self.eulagelesen = True
                self.configIni["Allgemein"]["eulagelesen"] = "True"
                with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                    self.configIni.write(configfile)
                logger.logger.info("EULA zugestimmt")
            else:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OpitGDT", "Ohne Zustimmung der Lizenzvereinbarung kann OpitGDT nicht gestartet werden.", QMessageBox.StandardButton.Ok)
                mb.exec()
                sys.exit()

        # Grundeinstellungen bei erstem Start
        if ersterStart:
            logger.logger.info("Erster Start")
            mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Vermutlich starten Sie OptiGDT das erste Mal auf diesem PC.\nMöchten Sie jetzt die Grundeinstellungen vornehmen?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            mb.setDefaultButton(QMessageBox.StandardButton.Yes)
            if mb.exec() == QMessageBox.StandardButton.Yes:
                ## Nur mit Lizenz
                self.einstellungenLanrLizenzschluessel(False, False)
                ## /Nur mit Lizenz
                self.einstellungenOptimierung(False, False)
                self.einstellungenGdt(False, False)
                self.einstellungenAllgemein(False, False)
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Die Ersteinrichtung ist abgeschlossen. OptiGDGT wird beendet.", QMessageBox.StandardButton.Ok)
                mb.exec()
                sys.exit()

        # Version vergleichen und gegebenenfalls aktualisieren
        configIniBase = configparser.ConfigParser()
        try:
            configIniBase.read(os.path.join(basedir, "config.ini"))
            if versionVeraltet(self.version, configIniBase["Allgemein"]["version"]):
                # Version aktualisieren
                self.configIni["Allgemein"]["version"] = configIniBase["Allgemein"]["version"]
                self.configIni["Allgemein"]["releasedatum"] = configIniBase["Allgemein"]["releasedatum"] 
                # config.ini aktualisieren
                # 2.1.3 -> 2.2.0: ["Optimierung"]["punktinkomma6220"] hinzufügen
                if not self.configIni.has_option("Optimierung", "punktinkomma6220"):
                    self.configIni["Optimierung"]["punktinkomma6220"] = "False"
                # 2.2.0 -> 2.3.0
                if not self.configIni.has_option("Allgemein", "autoupdate"):
                    self.configIni["Allgemein"]["autoupdate"] = "True"
                # 2.6.1 -> 2.7.0
                if not self.configIni.has_option("GDT", "gdtimportverzeichnissekundaer"):
                    self.configIni["GDT"]["gdtimportverzeichnissekundaer"] = ""
                # 2.7.3 - 2.7.5
                if not self.configIni.has_option("Optimierung", "sekundaeresimportverzeichnispruefen"):
                    self.configIni["Optimierung"]["sekundaeresimportverzeichnispruefen"] = "False"
                # 2.8.2 -> 2.9.0 ["Allgemein"]["updaterpfad"] hinzufügen
                if not self.configIni.has_option("Allgemein", "updaterpfad"):
                    self.configIni["Allgemein"]["updaterpfad"] = ""
                # /config.ini aktualisieren

                with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                    self.configIni.write(configfile)
                self.version = self.configIni["Allgemein"]["version"]
                logger.logger.info("Version auf " + self.version + " aktualisiert")
                # Prüfen, ob EULA gelesen
                de = dialogEula.Eula(self.version)
                de.exec()
                self.eulagelesen = de.checkBoxZustimmung.isChecked()
                self.configIni["Allgemein"]["eulagelesen"] = str(self.eulagelesen)
                with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                    self.configIni.write(configfile)
                if self.eulagelesen:
                    logger.logger.info("EULA zugestimmt")
                else:
                    logger.logger.info("EULA nicht zugestimmt")
                    mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Ohne  Zustimmung zur Lizenzvereinbarung kann OptiGDT nicht gestartet werden.", QMessageBox.StandardButton.Ok)
                    mb.exec()
                    sys.exit()
        except SystemExit:
            sys.exit()
        except:
            logger.logger.error("Problem beim Aktualisieren auf Version " + configIniBase["Allgemein"]["version"])
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Problem beim Aktualisieren auf Version " + configIniBase["Allgemein"]["version"], QMessageBox.StandardButton.Ok)
            mb.exec()

        self.addOnsFreigeschaltet = True
        
        # Nur mit Lizenz
        # Pseudo-Lizenz?
        self.pseudoLizenzId = ""
        rePatId = r"^patid\d+$"
        for arg in sys.argv:
            if re.match(rePatId, arg) != None:
                logger.logger.info("Pseudo-Lizenz mit id " + arg[5:])
                self.pseudoLizenzId = arg[5:]

        # Add-Ons freigeschaltet?
        self.addOnsFreigeschaltet = gdttoolsL.GdtToolsLizenzschluessel.lizenzErteilt(self.lizenzschluessel, self.lanr, gdttoolsL.SoftwareId.OPTIGDT) or gdttoolsL.GdtToolsLizenzschluessel.lizenzErteilt(self.lizenzschluessel, self.lanr, gdttoolsL.SoftwareId.OPTIGDTPSEUDO) and self.pseudoLizenzId != ""
        if self.lizenzschluessel != "" and gdttoolsL.GdtToolsLizenzschluessel.getSoftwareId(self.lizenzschluessel) == gdttoolsL.SoftwareId.OPTIGDTPSEUDO and self.pseudoLizenzId == "":
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Bei Verwendung einer Pseudolizenz muss OptiGDT mit einer Patienten-Id als Startargument im Format \"patid<Pat.-Id>\" ausgeführt werden.", QMessageBox.StandardButton.Ok)
            mb.exec() 
        ## /Nur mit Lizenz
        
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
        self.optimierungDuplizierenAction = QAction("Optimierung duplizieren", self)
        self.optimierungDuplizierenAction.triggered.connect(self.optimierungDuplizieren) # type:ignore
        self.treeWidgetOptimiert.addAction(self.optimierungDuplizierenAction)
        self.optimierungEntfernenAction = QAction("Optimierung entfernen", self)
        self.optimierungEntfernenAction.triggered.connect(self.optimierungEntfernen) # type:ignore
        self.treeWidgetOptimiert.addAction(self.optimierungEntfernenAction)

        # Optimierungsbuttons
        labelOptimierungen = QLabel("Optimierung:")
        labelOptimierungen.setFont(self.fontBold)
        self.pushButtonZeileHinzufuegen = QPushButton("Zeile hinzufügen")
        self.pushButtonZeileHinzufuegen.setFont(self.fontNormal)
        self.pushButtonZeileHinzufuegen.clicked.connect(lambda checked=False, optimierungsId="": self.optimierenMenuZeileHinzufuegen(checked, optimierungsId)) 
        self.pushButtonZeileAendern = QPushButton("Zeile ändern")
        self.pushButtonZeileAendern.setFont(self.fontNormal)
        self.pushButtonZeileAendern.clicked.connect(lambda checked=False, optimierungsId="": self.optimierenMenuZeileAendern(checked, optimierungsId)) 
        self.pushButtonZeileEntfernen = QPushButton("Zeile(n) entfernen")
        self.pushButtonZeileEntfernen.setFont(self.fontNormal)
        self.pushButtonZeileEntfernen.clicked.connect(lambda checked=False, optimierungsId="": self.optimierenMenuZeileEntfernen(checked, optimierungsId)) 
        self.pushButtonTestAendern = QPushButton("Test ändern")
        self.pushButtonTestAendern.setFont(self.fontNormal)
        self.pushButtonTestAendern.clicked.connect(lambda checked=False, optimierungsId="": self.optimierenMenuTestAendern(checked, optimierungsId)) 
        self.pushButtonTestEntfernen = QPushButton("Test entfernen")
        self.pushButtonTestEntfernen.setFont(self.fontNormal)
        self.pushButtonTestEntfernen.clicked.connect(lambda checked=False, optimierungsId="": self.optimierenMenuTestEntfernen(checked, optimierungsId)) 
        self.pushButtonTestAus6228 = QPushButton("Test aus 6228-Zeile")
        self.pushButtonTestAus6228.setFont(self.fontNormal)
        self.pushButtonTestAus6228.clicked.connect(lambda checked=False, duplizieren=False, optimierungsId="": self.optimierenMenuTestAus6228(checked, duplizieren, optimierungsId))
        self.pushButtonBefundAusTest = QPushButton("Befund aus Test")
        self.pushButtonBefundAusTest.setFont(self.fontNormal)
        self.pushButtonBefundAusTest.clicked.connect(lambda checked=False, optimierungsId="": self.optimierenMenuBefundAusTest(checked, optimierungsId))
        self.pushButtonInhalteZusammenfuehren = QPushButton("Inhalte zusammenführen")
        self.pushButtonInhalteZusammenfuehren.setFont(self.fontNormal)
        self.pushButtonInhalteZusammenfuehren.clicked.connect(lambda checked=False, optimierungsId="": self.optimierenMenuInhalteZusammenfuehren(checked, optimierungsId)) 
        self.pushButtonPdfHinzufuegen = QPushButton("PDF-Datei hinzufügen")
        self.pushButtonPdfHinzufuegen.setFont(self.fontNormal)
        self.pushButtonPdfHinzufuegen.clicked.connect(lambda checked=False, optimierungsId="": self.optimierenMenuPdfHinzufuegen(checked, optimierungsId)) 

        # Template-Infos
        templateInfosLayout = QGridLayout()
        groupBoxTemplateInfos = QGroupBox("Template-Infos")
        groupBoxTemplateInfos.setFont(self.fontBold)
        groupBoxTemplateInfos.setLayout(templateInfosLayout)
        labelName = QLabel("Name")
        labelName.setFont(self.fontNormal)
        self.lineEditName = QLineEdit()
        self.lineEditName.setFont(self.fontNormal)
        self.lineEditName.textEdited.connect(self.lineEditTemplateInfoChanged)
        labelKennfeld = QLabel("Gerätespezifisches Kennfeld")
        labelKennfeld.setFont(self.fontNormal)
        self.lineEditKennfeld = QLineEdit()
        self.lineEditKennfeld.setFont(self.fontNormal)
        self.lineEditKennfeld.textEdited.connect(self.lineEditTemplateInfoChanged)
        labelGdtId = QLabel("GDT-ID")
        labelGdtId.setFont(self.fontNormal)
        self.lineEditGdtId = QLineEdit()
        self.lineEditGdtId.setFont(self.fontNormal)
        self.lineEditGdtId.textEdited.connect(self.lineEditTemplateInfoChanged)
        labelGdtDateiname = QLabel("GDT-Dateiname")
        labelGdtDateiname.setFont(self.fontNormal)
        self.lineEditGdtDateiname = QLineEdit()
        self.lineEditGdtDateiname.setFont(self.fontNormal)
        self.lineEditGdtDateiname.textEdited.connect(self.lineEditTemplateInfoChanged)
        self.checkboxImmerGdtAlsExportDateiendung = QCheckBox("Immer \".gdt\" als Export-Dateiendung\u00b2")
        self.checkboxImmerGdtAlsExportDateiendung.setFont(self.fontNormal)
        labelExportverzeichnis = QLabel("Exportverzeichnis")
        labelExportverzeichnis.setFont(self.fontNormal)
        self.lineEditExportverzeichnis = QLineEdit()
        self.lineEditExportverzeichnis.setFont(self.fontNormal)
        self.lineEditExportverzeichnis.setReadOnly(True)
        self.lineEditExportverzeichnis.textChanged.connect(self.lineEditTemplateInfoChanged) 
        self.checkBoxKennfeld = QCheckBox("PR\u00b9")
        self.checkBoxKennfeld.setFont(self.fontNormal)
        self.checkBoxKennfeld.setToolTip("Prüfungsrelevant")
        self.checkBoxKennfeld.stateChanged.connect(self.checkBoxKennfeldChanged) 
        self.checkBoxGdtId = QCheckBox("PR\u00b9")
        self.checkBoxGdtId.setFont(self.fontNormal)
        self.checkBoxGdtId.setToolTip("Prüfungsrelevant")
        self.checkBoxGdtId.stateChanged.connect(self.checkBoxGdtIdChanged) 
        self.pushButtonExportverzeichnis = QPushButton("...")
        self.pushButtonExportverzeichnis.setFont(self.fontNormal)
        self.pushButtonExportverzeichnis.setToolTip("Durchsuchen")
        self.pushButtonExportverzeichnis.clicked.connect(self.pushButtonExportverzeichnisClicked) 
        labelFussnote1 = QLabel("\u00b9 Prüfungsrelevant: wird vor Anwendung des Templates neben dem GDT-Dateinamen auf Übereinstimmung geprüft")
        labelFussnote1.setFont(self.fontNormal)
        labelFussnote2 = QLabel("\u00b2 Diese Option kann zu Konflikten beim Ex-/ Importvorgang führen.")
        labelFussnote2.setFont(self.fontNormal)

        templateInfosLayout.addWidget(labelName, 0, 0, 1, 1)
        templateInfosLayout.addWidget(self.lineEditName, 0, 1, 1, 2)
        templateInfosLayout.addWidget(labelKennfeld, 1, 0, 1, 1)
        templateInfosLayout.addWidget(self.lineEditKennfeld, 1, 1, 1, 2)
        templateInfosLayout.addWidget(self.checkBoxKennfeld, 1, 3)
        templateInfosLayout.addWidget(labelGdtId, 2, 0)
        templateInfosLayout.addWidget(self.lineEditGdtId, 2, 1, 1, 2)
        templateInfosLayout.addWidget(self.checkBoxGdtId, 2, 3)
        templateInfosLayout.addWidget(labelGdtDateiname, 3, 0)
        templateInfosLayout.addWidget(self.lineEditGdtDateiname, 3, 1)
        templateInfosLayout.addWidget(self.checkboxImmerGdtAlsExportDateiendung, 3, 2)
        templateInfosLayout.addWidget(labelExportverzeichnis, 4, 0)
        templateInfosLayout.addWidget(self.lineEditExportverzeichnis, 4, 1, 1, 2)
        templateInfosLayout.addWidget(self.pushButtonExportverzeichnis, 4, 3)
        templateInfosLayout.addWidget(labelFussnote1, 5, 0, 1, 4)
        templateInfosLayout.addWidget(labelFussnote2, 6, 0, 1, 4)

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
        optimierungsButtonsLayout.addWidget(self.pushButtonPdfHinzufuegen)
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
        self.optimierungDuplizierenAction.setEnabled(False)
        self.optimierungEntfernenAction.setEnabled(False)

        logger.logger.info("Eingabeformular aufgebaut")

        # Menü
        menubar = self.menuBar()
        anwendungMenu = menubar.addMenu("")
        aboutAction = QAction(self)
        aboutAction.setMenuRole(QAction.MenuRole.AboutRole)
        aboutAction.triggered.connect(self.ueberOptiGdt) 
        updateAction = QAction("Jetzt auf Update prüfen", self)
        updateAction.setMenuRole(QAction.MenuRole.ApplicationSpecificRole)
        updateAction.triggered.connect(self.updatePruefung) 
        gdtDateiMenu = menubar.addMenu("GDT-Datei")
        gdtDateiMenuOeffnenAction = QAction("Öffnen", self)
        gdtDateiMenuOeffnenAction.triggered.connect(lambda checked = False: self.gdtDateiMenuOeffnen(checked)) 
        gdtDateiMenuOeffnenAction.setShortcut(QKeySequence("Ctrl+G"))
        gdtDateiMenuSchliessenAction = QAction("Schließen", self)
        gdtDateiMenuSchliessenAction.triggered.connect(self.gdtDateiMenuSchliessen) 
        templateMenu = menubar.addMenu("Template")
        templateMenuLadenAction = QAction("Laden", self)
        templateMenuLadenAction.triggered.connect(self.templateMenuLaden) 
        templateMenuLadenAction.setShortcut(QKeySequence("Ctrl+T"))
        templateMenuSpeichernAction = QAction("Speichern", self)
        templateMenuSpeichernAction.triggered.connect(self.templateMenuSpeichern) 
        templateMenuTemplatesVerwaltenAction = QAction("Templates verwalten", self)
        templateMenuTemplatesVerwaltenAction.triggered.connect(self.templateMenuTemplatesVerwalten) 
        optimierenMenu = menubar.addMenu("Optimieren")
        optimierenMenuZeileHinzufuegenAction = QAction("Zeile hinzufügen", self)
        optimierenMenuZeileHinzufuegenAction.triggered.connect(lambda checked=False, optimierungsId="": self.optimierenMenuZeileHinzufuegen(checked, optimierungsId))
        optimierenMenuZeileAendernAction = QAction("Zeile ändern", self)
        optimierenMenuZeileAendernAction.triggered.connect(lambda checked=False, optimierungsId="": self.optimierenMenuZeileAendern(checked, optimierungsId)) 
        optimierenMenuZeileEntfernenAction = QAction("Zeile(n) entfernen", self)
        optimierenMenuZeileEntfernenAction.triggered.connect(lambda checked=False, optimierungsId="": self.optimierenMenuZeileEntfernen(checked, optimierungsId)) 
        optimierenMenuTestAendernAction = QAction("Test ändern", self)
        optimierenMenuTestAendernAction.triggered.connect(lambda checked=False, optimierungsId="": self.optimierenMenuTestAendern(checked, optimierungsId)) 
        optimierenMenuTestEntfernenAction = QAction("Test entfernen", self)
        optimierenMenuTestEntfernenAction.triggered.connect(lambda checked=False, optimierungsId="": self.optimierenMenuTestEntfernen(checked, optimierungsId)) 
        optimierenMenuTestAus6228Action = QAction("Test aus 6228-Zeile", self)
        optimierenMenuTestAus6228Action.triggered.connect(lambda checked=False, duplizieren=False, optimierungsId="": self.optimierenMenuTestAus6228(checked, duplizieren, optimierungsId)) 
        optimierenMenuBefundAusTestAction = QAction("Befundzeile aus Test(s)", self)
        optimierenMenuBefundAusTestAction.triggered.connect(lambda checked=False, optimierungsId="": self.optimierenMenuBefundAusTest(checked, optimierungsId))
        optimierenMenuInhalteZusammenfuehrenAction = QAction("Inhalte zusammenführen", self)
        optimierenMenuInhalteZusammenfuehrenAction.triggered.connect(lambda checked=False, optimierungsId="": self.optimierenMenuInhalteZusammenfuehren(checked, optimierungsId)) 
        optimierenMenuPdfHinzufuegenAction = QAction("PDF-Datei hinzufügen", self)
        optimierenMenuPdfHinzufuegenAction.triggered.connect(lambda checked=False, optimierungsId="": self.optimierenMenuPdfHinzufuegen(checked, optimierungsId)) 
        self.optimierenMenuVerzeichnisueberwachungStartenAction = QAction("Verzeichnisüberwachung starten", self)
        self.optimierenMenuVerzeichnisueberwachungStartenAction.triggered.connect(self.optimierenMenuVerzeichnisueberwachungStarten) 
        self.optimierenMenuInDenHintergrundAction = QAction("OptiGDT im Hintergrund ausführen", self)
        self.optimierenMenuInDenHintergrundAction.triggered.connect(self.optimierenMenuInDenHintergrund) 
        self.optimierenMenuInDenHintergrundAction.setEnabled(False)

        einstellungenMenu = menubar.addMenu("Einstellungen")
        einstellungenAllgemeinAction = QAction("Allgemeine Einstellungen", self)
        einstellungenAllgemeinAction.triggered.connect(lambda checked = False, neustartfrage = True: self.einstellungenAllgemein(checked, neustartfrage))
        einstellungenOptimierungAction = QAction("Optimierung", self)
        einstellungenOptimierungAction.triggered.connect(lambda checked = False, neustartfrage = True: self.einstellungenOptimierung(checked, neustartfrage))
        einstellungenGdtAction = QAction("GDT", self)
        einstellungenGdtAction.triggered.connect(lambda checked = False, neustartfrage = True: self.einstellungenGdt(checked, neustartfrage))
        ## Nur mit Lizenz
        einstellungenErweiterungenAction = QAction("LANR/Lizenzschlüssel", self)
        einstellungenErweiterungenAction.triggered.connect(lambda checked = False, neustartfrage = True: self.einstellungenLanrLizenzschluessel(checked, neustartfrage))
        einstellungenImportExportAction = QAction("Im- /Exportieren", self)
        einstellungenImportExportAction.triggered.connect(self.einstellungenImportExport)
        einstellungenImportExportAction.setShortcut(QKeySequence("Ctrl+I"))
        einstellungenImportExportAction.setMenuRole(QAction.MenuRole.NoRole)
        ## /Nur mit Lizenz
        hilfeMenu = menubar.addMenu("Hilfe")
        hilfeWikiAction = QAction("OptiGDT Wiki", self)
        hilfeWikiAction.triggered.connect(self.optigdtWiki) 
        hilfeUpdateAction = QAction("Jetzt auf Update prüfen", self)
        hilfeUpdateAction.triggered.connect(self.updatePruefung) 
        hilfeAutoUpdateAction = QAction("Automatisch auf Update prüfen", self)
        hilfeAutoUpdateAction.setCheckable(True)
        hilfeAutoUpdateAction.setChecked(self.autoupdate)
        hilfeAutoUpdateAction.triggered.connect(self.autoUpdatePruefung)
        hilfeUeberAction = QAction("Über OptiGDT", self)
        hilfeUeberAction.setMenuRole(QAction.MenuRole.NoRole)
        hilfeUeberAction.triggered.connect(self.ueberOptiGdt)
        hilfeEulaAction = QAction("Lizenzvereinbarung (EULA)", self)
        hilfeEulaAction.triggered.connect(self.eula) 
        hilfeLogExportieren = QAction("Log-Verzeichnis exportieren", self)
        hilfeLogExportieren.triggered.connect(self.logExportieren) 
        
        anwendungMenu.addAction(aboutAction)
        anwendungMenu.addAction(updateAction)

        gdtDateiMenu.addAction(gdtDateiMenuOeffnenAction)
        gdtDateiMenu.addAction(gdtDateiMenuSchliessenAction)
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
        optimierenMenu.addAction(optimierenMenuPdfHinzufuegenAction)
        optimierenMenu.addSeparator()
        optimierenMenu.addAction(self.optimierenMenuVerzeichnisueberwachungStartenAction)
        optimierenMenu.addAction(self.optimierenMenuInDenHintergrundAction)
        einstellungenMenu.addAction(einstellungenAllgemeinAction)
        einstellungenMenu.addAction(einstellungenOptimierungAction)
        einstellungenMenu.addAction(einstellungenGdtAction)
        ## Nur mit Lizenz
        einstellungenMenu.addAction(einstellungenErweiterungenAction)
        einstellungenMenu.addAction(einstellungenImportExportAction)
        ## /Nur mit Lizenz

        hilfeMenu.addAction(hilfeWikiAction)
        hilfeMenu.addSeparator()
        hilfeMenu.addAction(hilfeUpdateAction)
        hilfeMenu.addAction(hilfeAutoUpdateAction)
        hilfeMenu.addSeparator()
        hilfeMenu.addAction(hilfeUeberAction)
        hilfeMenu.addAction(hilfeEulaAction)
        hilfeMenu.addSeparator()
        hilfeMenu.addAction(hilfeLogExportieren)

        # Updateprüfung auf Github
        if self.autoupdate:
            try:
                self.updatePruefung(meldungNurWennUpdateVerfuegbar=True)
            except Exception as e:
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Updateprüfung nicht möglich.\nBitte überprüfen Sie Ihre Internetverbindung.", QMessageBox.StandardButton.Ok)
                mb.exec()
                logger.logger.warning("Updateprüfung nicht möglich: " + str(e))
        
        # Autostart?
        if len(sys.argv) > 1 and "ue" in sys.argv:
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
                if typ == "addZeile" or typ == "addPdf":
                    self.setTreeWidgetItemHintergrund(item, treeWidget.columnCount(), farbe.getTextColor(farbe.farben.ADDZEILE, self.palette()))
                elif typ == "changeZeile":
                    self.setTreeWidgetItemHintergrund(item, treeWidget.columnCount(), farbe.getTextColor(farbe.farben.CHANGEZEILE, self.palette()))
                elif typ == "deleteZeile":
                    item.setFont(2, self.fontDurchgestrichen)
                elif typ == "deleteTest":
                    item.setFont(2, self.fontDurchgestrichen)
                elif typ == "changeTest":
                    self.setTreeWidgetItemHintergrund(item, treeWidget.columnCount(), farbe.getTextColor(farbe.farben.CHANGETEST, self.palette()))
                elif typ == "testAus6228":
                    #self.setTreeWidgetItemHintergrund(item, treeWidget.columnCount(), testAus6228Hintergrund) (bis 2.12.0)
                    self.setTreeWidgetItemHintergrund(item, treeWidget.columnCount(), farbe.getTextColor(farbe.farben.TESTAUS6228, self.palette()))
                elif typ == "befundAusTest":
                    self.setTreeWidgetItemHintergrund(item, treeWidget.columnCount(), farbe.getTextColor(farbe.farben.BEFUNDAUSTEST, self.palette()))
                elif typ == "concatInhalte":
                    self.setTreeWidgetItemHintergrund(item, treeWidget.columnCount(), farbe.getTextColor(farbe.farben.CONCAT, self.palette()))
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
            if current.text(0).strip() in self.optimierungsIds:
                optimierungstyp = class_optimierung.Optimierung.getTypVonId(self.templateRootElement, self.optimierungsIds[current.text(0).strip()])
                self.optimierungDuplizierenAction.setEnabled(optimierungstyp == "testAus6228")
            treeWidget = current.treeWidget()
            # Farbiger Hintergrund für Tests
            for index in range(treeWidget.topLevelItemCount()):
                if treeWidget.topLevelItem(index).background(0).color() == farbe.getTextColor(farbe.farben.TESTAUSAHL, self.palette()):
                    self.setTreeWidgetZeileHintergrund(treeWidget, index, farbe.getTextColor(farbe.farben.NORMAL, self.palette()))
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
                        if treeWidget.topLevelItem(i + ersteTestItemNummer).background(0).color() != farbe.getTextColor(farbe.farben.CHANGETEST, self.palette()) and treeWidget.topLevelItem(i + ersteTestItemNummer).background(0).color() != farbe.getTextColor(farbe.farben.TESTAUS6228, self.palette()):
                            self.setTreeWidgetZeileHintergrund(treeWidget, i + ersteTestItemNummer, farbe.getTextColor(farbe.farben.TESTAUSAHL, self.palette()))
        else:
            self.optimierungBearbeitenAction.setEnabled(False)
            self.optimierungDuplizierenAction.setEnabled(False)
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
            self.lineEditExportverzeichnis.setText(os.path.abspath(fd.directory().path()))
            self.lineEditExportverzeichnis.setToolTip(os.path.abspath(fd.directory().path()))

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
    def einstellungenAllgemein(self, checked, neustartfrage):
        de = dialogEinstellungenAllgemein.EinstellungenAllgemein(self.configPath)
        if de.exec() == 1:
            self.configIni["Allgemein"]["updaterpfad"] = de.lineEditUpdaterPfad.text()
            self.configIni["Allgemein"]["autoupdate"] = str(de.checkBoxAutoUpdate.isChecked())
            with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                self.configIni.write(configfile)
            if neustartfrage:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Damit die Einstellungsänderungen wirksam werden, sollte OptiGDT neu gestartet werden.\nSoll OptiGDT jetzt neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    os.execl(sys.executable, __file__, *sys.argv)

    def einstellungenOptimierung(self, checked, neustartfrage):
        de = dialogEinstellungenOptimierung.EinstellungenOptimierung(self.configPath)
        if de.exec() == 1:
            self.configIni["Optimierung"]["standardtemplateverzeichnis"] = de.lineEditTemplateverzeichnis.text().strip()
            self.configIni["Optimierung"]["sekundenbistemplatebearbeitung"] = de.lineEditVerzoegerung.text().strip()
            self.configIni["Optimierung"]["maxeindeutigkeitskriterien"] = de.lineEditMaxEindutigkeitskriterien.text().strip()
            self.configIni["Optimierung"]["maxtestaenderungen"] = de.lineEditMaxAenderungenProTest.text().strip()
            self.configIni["Optimierung"]["maxanzahl6228spalten"] = de.lineEditMaxAnzahl6228Spalten.text().strip()
            self.configIni["Optimierung"]["standard6228trennregexpattern"] = de.lineEditStandardSpaltenTrennzeichen.text().strip()
            self.configIni["Optimierung"]["punktinkomma6220"] = str(de.checkboxPunktInKomma.isChecked())

            with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                self.configIni.write(configfile)
            if neustartfrage:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Damit die Einstellungsänderungen wirksam werden, sollte OptiGDT neu gestartet werden.\nSoll OptiGDT jetzt neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    self.tray.hide()
                    os.execl(sys.executable, __file__, *sys.argv)
        
    def einstellungenGdt(self, checked, neustartfrage):
        de = dialogEinstellungenGdt.EinstellungenGdt(self.configPath)
        if de.exec() == 1:
            self.configIni["GDT"]["gdtimportverzeichnis"] = de.lineEditImportPrimaer.text()
            self.configIni["GDT"]["gdtimportverzeichnissekundaer"] = de.lineEditImportSekundaer.text()
            self.configIni["Optimierung"]["sekundaeresimportverzeichnispruefen"] = str(de.checkBoxSekundaeresImportverzeichnisPruefen.isChecked())
            self.configIni["GDT"]["zeichensatz"] = str(de.aktuelleZeichensatznummer + 1)
            with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                self.configIni.write(configfile)
            if neustartfrage:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Damit die Einstellungsänderungen wirksam werden, sollte OptiGDT neu gestartet werden.\nSoll OptiGDT jetzt neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    self.tray.hide()
                    os.execl(sys.executable, __file__, *sys.argv)
    
    ## Nur mit Lizenz
    def einstellungenLanrLizenzschluessel(self, checked, neustartfrage):
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
                    self.tray.hide()
                    os.execl(sys.executable, __file__, *sys.argv)
    
    def einstellungenImportExport(self):
        de = dialogEinstellungenImportExport.EinstellungenImportExport(self.configPath)
        if de.exec() == 1:
            pass   
    ## /Nur mit Lizenz

    def optigdtWiki(self, link):
        QDesktopServices.openUrl("https://github.com/retconx/optigdt/wiki")

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
                
    # def updatePruefung(self, meldungNurWennUpdateVerfuegbar = False):
    #     response = requests.get("https://api.github.com/repos/retconx/optigdt/releases/latest")
    #     githubRelaseTag = response.json()["tag_name"]
    #     latestVersion = githubRelaseTag[1:] # ohne v
    #     if versionVeraltet(self.version, latestVersion):
    #         mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Die aktuellere OptiGDT-Version " + latestVersion + " ist auf <a href='https://github.com/retconx/optigdt/releases'>Github</a> verfügbar.", QMessageBox.StandardButton.Ok)
    #         mb.setTextFormat(Qt.TextFormat.RichText)
    #         mb.exec()
    #     elif not meldungNurWennUpdateVerfuegbar:
    #         mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Sie nutzen die aktuelle OptiGDT-Version.", QMessageBox.StandardButton.Ok)
    #         mb.exec()

    def updatePruefung(self, meldungNurWennUpdateVerfuegbar = False):
        logger.logger.info("Updateprüfung")
        response = requests.get("https://api.github.com/repos/retconx/optigdt/releases/latest")
        githubRelaseTag = response.json()["tag_name"]
        latestVersion = githubRelaseTag[1:] # ohne v
        if versionVeraltet(self.version, latestVersion):
            logger.logger.info("Bisher: " + self.version + ", neu: " + latestVersion)
            if os.path.exists(self.updaterpfad):
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Die aktuellere OptiGDT-Version " + latestVersion + " ist auf Github verfügbar.\nSoll der GDT-Tools Updater geladen werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    logger.logger.info("Updater wird geladen")
                    atexit.register(self.updaterLaden)
                    sys.exit()
            else:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Die aktuellere OptiGDT-Version " + latestVersion + " ist auf <a href='https://github.com/retconx/optigdt/releases'>Github</a> verfügbar.<br />Bitte beachten Sie auch die Möglichkeit, den Updateprozess mit dem <a href='https://github.com/retconx/gdttoolsupdater/wiki'>GDT-Tools Updater</a> zu automatisieren.", QMessageBox.StandardButton.Ok)
                mb.setTextFormat(Qt.TextFormat.RichText)
                mb.exec()
        elif not meldungNurWennUpdateVerfuegbar:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Sie nutzen die aktuelle OptiGDT-Version.", QMessageBox.StandardButton.Ok)
            mb.exec()

    def updaterLaden(self):
        sex = sys.executable
        programmverzeichnis = ""
        logger.logger.info("sys.executable: " + sex)
        if "win32" in sys.platform:
            programmverzeichnis = sex[:sex.rfind("optigdt.exe")]
        elif "darwin" in sys.platform:
            programmverzeichnis = sex[:sex.find("OptiGDT.app")]
        elif "linux" in sys.platform:
            programmverzeichnis = sex[:sex.rfind("optigdt")]
        logger.logger.info("Programmverzeichnis: " + programmverzeichnis)
        try:
            if "win32" in sys.platform:
                subprocess.Popen([self.updaterpfad, "optigdt", self.version, programmverzeichnis], creationflags=subprocess.DETACHED_PROCESS) # type: ignore
            elif "darwin" in sys.platform:
                subprocess.Popen(["open", "-a", self.updaterpfad, "--args", "optigdt", self.version, programmverzeichnis])
            elif "linux" in sys.platform:
                subprocess.Popen([self.updaterpfad, "optigdt", self.version, programmverzeichnis])
        except Exception as e:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Der GDT-Tools Updater konnte nicht gestartet werden", QMessageBox.StandardButton.Ok)
            logger.logger.error("Fehler beim Starten des GDT-Tools Updaters: " + str(e))
            mb.exec()

    def autoUpdatePruefung(self, checked):
        self.autoupdate = checked
        self.configIni["Allgemein"]["autoupdate"] = str(checked)
        with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
            self.configIni.write(configfile) 
    
    def ueberOptiGdt(self):
        de = dialogUeberOptiGdt.UeberOptiGdt()
        de.exec()

    def eula(self):
        QDesktopServices.openUrl("https://gdttools.de/Lizenzvereinbarung_OptiGDT.pdf")

    def gdtDateiMenuOeffnen(self, checked, referenzpfad:str=""):
        fortfahren = True
        if referenzpfad == "":
            if self.ungesichertesTemplate:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Beim Öffnen einer GDT-Datei gehen derzeit nicht gesicherte Daten verloren.\nWollen Sie dennoch fortfahren?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.No)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.No:
                    fortfahren = False
        if fortfahren:
            gdtDateiLaden = False
            gdtDateiPfad = referenzpfad
            if referenzpfad == "":
                fd = QFileDialog(self)
                fd.setFileMode(QFileDialog.FileMode.ExistingFile)
                fd.setWindowTitle("GDT-Datei laden")
                fd.setModal(True)
                fd.setViewMode(QFileDialog.ViewMode.Detail)
                dreistelligeNummern = []
                for i in range(1000):   
                    dreistelligeNummern.append("*.{:>03}".format(str(i)))
                filter = "*.gdt " + str.join(" ", dreistelligeNummern)
                fd.setNameFilters(["gdt-Dateien (" + filter + ")"])
                fd.setLabelText(QFileDialog.DialogLabel.Accept, "Ok")
                fd.setLabelText(QFileDialog.DialogLabel.Reject, "Abbrechen")
                if fd.exec() == 1:
                    gdtDateiPfad = fd.selectedFiles()[0]
                    gdtDateiLaden = True
            else:
                gdtDateiLaden = True
            if gdtDateiLaden:
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
                    self.checkboxImmerGdtAlsExportDateiendung.setChecked(False)
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

    def gdtDateiMenuSchliessen(self):
        schliessenOk = True
        if self.ungesichertesTemplate:
            mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Beim Schließen der GDT-Datei gehen derzeit nicht gesicherte Daten verloren.\nWollen Sie dennoch fortfahren?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            mb.setDefaultButton(QMessageBox.StandardButton.No)
            mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
            mb.button(QMessageBox.StandardButton.No).setText("Nein")
            if mb.exec() == QMessageBox.StandardButton.No:
                schliessenOk = False
        if schliessenOk:
            self.labelTreeViewUeberschriftLinks.setText("")
            self.labelTreeViewUeberschriftRechts.setText("")
            self.treeWidgetOriginal.clear()
            self.treeWidgetOptimiert.clear()
            self.lineEditName.setText("")
            self.lineEditKennfeld.setText("")
            self.lineEditGdtId.setText("")
            self.lineEditGdtDateiname.setText("")
            self.checkboxImmerGdtAlsExportDateiendung.setChecked(False)
            self.lineEditExportverzeichnis.setText("")
            self.checkBoxKennfeld.setChecked(False)
            self.checkBoxGdtId.setChecked(False)
            self.ungesichertesTemplate = False

    def templateMenuLaden(self):
        ladenOk = True
        if self.ungesichertesTemplate:
            mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Beim Laden eines Templates gehen derzeit nicht gesicherte Daten verloren.\nWollen Sie dennoch fortfahren?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            mb.setDefaultButton(QMessageBox.StandardButton.No)
            mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
            mb.button(QMessageBox.StandardButton.No).setText("Nein")
            if mb.exec() == QMessageBox.StandardButton.No:
                ladenOk = False
        if ladenOk:
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
                    # Ab Version 2.6.0
                    immerGdtAlsExportDateiendung = False
                    if templateRootElement.get("immergdtalsexportdateiendung") != None:
                        immerGdtAlsExportDateiendung = templateRootElement.get("immergdtalsexportdateiendung") == "True"
                    gdtDateiVorhanden = True
                    if self.treeWidgetOriginal.topLevelItemCount() == 0: # Keine GDT-Datei geladen
                        referenzGdtDateiname = os.path.join(self.configPath, "gdtreferenzen", os.path.basename(templatePfad)[:-4] + "_ref_" + gdtDateiname)
                        if os.path.exists(os.path.join(self.configPath, "gdtreferenzen", referenzGdtDateiname)):
                            self.gdtDateiMenuOeffnen(False, os.path.join(self.configPath, "gdtreferenzen", referenzGdtDateiname))
                            self.gdtDateipfad = referenzGdtDateiname.split("_ref_")[1]
                            logger.logger.info("Referenz-GDT-Datei " + os.path.join(self.configPath, "gdtreferenzen", templatePfad) + " geladen")
                        else:
                            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Das Template kann nicht geöffnet werden, da keine passende Referenz-GDT-Datei gefunden wurde.", QMessageBox.StandardButton.Ok)
                            mb.exec()
                            gdtDateiVorhanden = False
                    gdtDateinamePasst = False
                    endungGeladeneDatei = self.gdtDateipfad[-4:]
                    if endungGeladeneDatei.lower() == ".gdt":
                        gdtDateinamePasst = os.path.basename(self.gdtDateipfad) == gdtDateiname
                    elif re.match(reGdtDateiendungSequentiell, endungGeladeneDatei) != None:
                        gdtDateinamePasst = re.match(reGdtDateiendungSequentiell, gdtDateiname[-4:]) != None and os.path.basename(self.gdtDateipfad)[:-4] == gdtDateiname[:-4]
                    if gdtDateiVorhanden and gdtDateinamePasst:
                        self.templateRootElement = templateRootElement
                        exceptions = []
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
                        self.checkboxImmerGdtAlsExportDateiendung.setChecked(immerGdtAlsExportDateiendung)
                        self.lineEditExportverzeichnis.setText(exportverzeichnis)
                        self.ungesichertesTemplate = False
                        if len(exceptions) > 0:
                            exceptionListe = "\n-".join(exceptions)
                            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Template-Rückmeldung:\n-" + exceptionListe, QMessageBox.StandardButton.Ok)
                            mb.exec()
                    elif gdtDateiVorhanden:
                        mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Die Template-Datei passt nicht zur geladenen GDT-Datei.", QMessageBox.StandardButton.Ok)
                        mb.exec()
                except Exception as e:
                        mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Fehler beim Laden des Templates " + templatePfad + ": " + str(e), QMessageBox.StandardButton.Ok)
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
                    mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Das gerätespezifische Kennfeld für das Template sollte aus bis zu vier Buchstaben, gefolgt von zwei Ziffern bestehen.\nSoll es dennoch so übernommen werden (" + self.lineEditKennfeld.text().strip() + ")?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    mb.setDefaultButton(QMessageBox.StandardButton.No)
                    mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                    mb.button(QMessageBox.StandardButton.No).setText("Nein")
                    if mb.exec() == QMessageBox.StandardButton.No:
                        self.lineEditKennfeld.setFocus()
                        self.lineEditKennfeld.selectAll()
                        formularOk = False
            if formularOk and self.checkBoxGdtId.isChecked() and self.lineEditGdtId.text().strip() != "" and re.match(reGdtId, self.lineEditGdtId.text().strip()) == None:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Die GDT-ID für das Template sollte aus acht Zeichen bestehen.\nSoll sie dennoch so übernommen werden (" + self.lineEditGdtId.text().strip() + ")?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.No)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.No:
                    self.lineEditGdtId.setFocus()
                    self.lineEditGdtId.selectAll()
                    formularOk = False
            if formularOk and (self.lineEditGdtDateiname.text().strip() == "" or re.match(reGdtDateiendung, self.lineEditGdtDateiname.text().strip()[-4:].lower()) == None):
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Der GDT-Dateiname für das Template ist unzulässig.", QMessageBox.StandardButton.Ok)
                mb.exec()
                self.lineEditGdtDateiname.setFocus()
                self.lineEditGdtDateiname.selectAll()
                formularOk = False
            if formularOk and not os.path.exists(self.lineEditExportverzeichnis.text().strip()):
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Das Exportverzeichnis für das Template existiert nicht.", QMessageBox.StandardButton.Ok)
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
                    if os.path.exists(fd.selectedFiles()[0]):
                        mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Das Template \"" + self.lineEditName.text().strip() + "\" existiert bereits.\nSoll es überschrieben werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
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
                        gdtDateiname = self.lineEditGdtDateiname.text().strip()
                        self.templateRootElement.set("gdtDateiname", gdtDateiname)
                        self.templateRootElement.set("exportverzeichnis", self.lineEditExportverzeichnis.text())
                        self.templateRootElement.set("immergdtalsexportdateiendung", str(self.checkboxImmerGdtAlsExportDateiendung.isChecked())) # Ab Version 2.6.0
                        et = ElementTree.ElementTree(self.templateRootElement)
                        ElementTree.indent(et)
                        try:
                            et.write(fd.selectedFiles()[0], "utf-8", True)
                            self.ungesichertesTemplate = False
                        except Exception as e:
                            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Fehler beim Sepichern des Templates: " + str(e), QMessageBox.StandardButton.Ok)
                            mb.exec()
                    # GDT-Datei als Referenz speichern
                        if not os.path.exists(os.path.join(self.configPath, "gdtreferenzen")):
                            os.mkdir(os.path.join(self.configPath, "gdtreferenzen"), 0o777)
                        referenzdateiname = self.lineEditName.text() + "_ref_" + gdtDateiname
                        pfad = os.path.join(self.configPath, "gdtreferenzen", referenzdateiname)
                        if self.gdtDateiOriginal.speichern(pfad, self.zeichensatz):
                            logger.logger.info("GDT-Datei " + referenzdateiname + " als Referenz gespeichet")
                        else: 
                            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Fehler beim Speichern der GDT-Datei " + referenzdateiname + " als Referenzdatei", QMessageBox.StandardButton.Ok)
                            mb.exec()
                            logger.logger.error("Fehler beim Speichern der GDT-Datei " + referenzdateiname + " als Referenz in " + pfad)
            elif self.treeWidgetOriginal.topLevelItemCount() == 0:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Keine GDT-Datei geladen", QMessageBox.StandardButton.Ok)
                mb.exec()
        else:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Kein Template definiert. Bitte führen Sie zumindest eine Optimierung durch.", QMessageBox.StandardButton.Ok)
            mb.exec()

    def templateMenuTemplatesVerwalten(self):
        dg = dialogTemplatesVerwalten.TemplatesVerwalten(self.standardTemplateVerzeichnis)
        if dg.exec() == 1:
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
                    
            # Templates löschen
            for i in range(len(dg.templatenamen)):
                if dg.checkBoxLoeschen[i].isChecked():
                    mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Soll das Template \"" + dg.lineEditName[i].text() + "\" endgültig gelöscht werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    mb.setDefaultButton(QMessageBox.StandardButton.No)
                    mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                    mb.button(QMessageBox.StandardButton.No).setText("Nein")
                    if mb.exec() == QMessageBox.StandardButton.Yes:
                        try:
                            os.unlink(os.path.join(self.standardTemplateVerzeichnis, dg.lineEditName[i].text().strip() + ".ogt"))
                            logger.logger.info("Template " + os.path.join(self.standardTemplateVerzeichnis, dg.lineEditName[i].text().strip() + ".ogt") + " gelöscht")
                        except Exception as e:
                            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Fehler beim Löschen des Templates \"" + os.path.join(self.standardTemplateVerzeichnis, dg.lineEditName[i].text().strip() + ".ogt") + "\": " + str(e), QMessageBox.StandardButton.Ok)
                            mb.exec()

    def optimierenMenuZeileHinzufuegen(self, checked, optimierungsId:str=""):
        if self.addOnsFreigeschaltet:
            feldkennung = ""
            inhalt = ""
            zeilennummer = -1
            # Optimierungselement finden, wenn bereits vorhanden (bearbeiten)
            if optimierungsId != "":
                for optimierungElement in self.templateRootElement.findall("optimierung"):
                    if str(optimierungElement.get("id")) == optimierungsId:
                        feldkennung = str(optimierungElement.find("feldkennung").text) # type:ignore
                        inhalt = str(optimierungElement.find("inhalt").text) # type:ignore
                        if optimierungElement.find("zeilennummer") != None: #  ab 2.13.0
                            zeilennummer = int(str(optimierungElement.find("zeilennummer").text)) # type:ignore
                        break
            if self.treeWidgetOriginal.topLevelItemCount() > 0:
                do = dialogOptimierungAddZeile.OptimierungAddZeile(self.gdtDateiOriginal, feldkennung, inhalt, zeilennummer)
                if do.exec() == 1:
                    zeilennummer = -1
                    if do.lineEditZeilennummer.text() != "":
                        zeilennummer = int(do.lineEditZeilennummer.text())
                    self.templateRootDefinieren()
                    optimierungElement = class_optimierung.OptiAddZeile(do.lineEditFeldkennung.text(), do.lineEditInhalt.text(), zeilennummer, self.templateRootElement)
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
        if len(self.gdtDateiOriginal.getTests()) > 0:
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
        else:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Die geladene GDT-Datei enthält keine Tests.", QMessageBox.StandardButton.Ok)
            mb.exec()

    def optimierenMenuTestEntfernen(self, checked, optimierungsId:str=""):
        if len(self.gdtDateiOriginal.getTests()) > 0:
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
        else:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Die geladene GDT-Datei enthält keine Tests.", QMessageBox.StandardButton.Ok)
            mb.exec()

    def optimierenMenuTestAus6228(self, checked, duplizieren:bool, optimierungsId:str=""):
        if self.addOnsFreigeschaltet:
            trennRegexPattern = ""
            erkennungstext = ""
            erkennungsspalte = 0
            ergebnisspalte = 0
            eindeutigkeitErzwingen = True
            ntesVorkommen = 1
            testIdent = ""
            testBezeichnung = ""
            testEinheit = ""
            angepassteErgebnisseDict = {}
            # Optimierungselement finden, wenn bereits vorhanden (bearbeiten)
            if optimierungsId != "":
                for optimierungElement in self.templateRootElement.findall("optimierung"):
                    if str(optimierungElement.get("id")) == optimierungsId:
                        trennRegexPattern = str(optimierungElement.find("trennRegexPattern").text) # type:ignore
                        erkennungstext = str(optimierungElement.find("erkennungstext").text) # type:ignore
                        if erkennungstext == "None":
                            erkennungstext = ""
                        erkennungsspalte = int(optimierungElement.find("erkennungsspalte").text) # type:ignore
                        ergebnisspalte = int(optimierungElement.find("ergebnisspalte").text) # type:ignore
                        if optimierungElement.find("eindeutigkeiterzwingen") != None: # ab 2.10.1
                            eindeutigkeitErzwingen = optimierungElement.find("eindeutigkeiterzwingen").text == "True" # type:ignore
                        if optimierungElement.find("ntesvorkommen") != None: # ab 2.10.1
                            ntesVorkommen = int(optimierungElement.find("ntesvorkommen").text) # type:ignore
                        testIdent = str(optimierungElement.find("testIdent").text) # type:ignore
                        testBezeichnung = str(optimierungElement.find("testBezeichnung").text) # type:ignore
                        testEinheit = str(optimierungElement.find("testEinheit").text) # type:ignore
                        if testEinheit == "None":
                            testEinheit = ""
                        if optimierungElement.find("angepassteergebnisse") != None: # ab 2.12.0
                            angepassteErgebnisseElement = optimierungElement.find("angepassteergebnisse")
                            for ergebnisElement in angepassteErgebnisseElement.findall("ergebnis"): # type:ignore
                                original = ergebnisElement.find("original").text # type:ignore
                                angepasst = ergebnisElement.find("angepasst").text # type:ignore
                                angepassteErgebnisseDict[original] = angepasst
                        break
            if self.treeWidgetOriginal.topLevelItemCount() > 0:
                if len(self.gdtDateiOriginal.getInhalte("6228")) > 0:
                    do = dialogOptimierungTestAus6228.OptimierungTestAus6228(self.gdtDateiOptimiert, duplizieren, trennRegexPattern, erkennungstext, erkennungsspalte, ergebnisspalte, eindeutigkeitErzwingen, ntesVorkommen, testIdent, testBezeichnung, testEinheit, self.standard6228trennregexpattern, self.maxAnzahl6228Spalten, angepassteErgebnisseDict)
                    if do.exec() == 1:
                        self.templateRootDefinieren()
                        optimierungElement = class_optimierung.OptiTestAus6228(do.lineEditTrennRegexPattern.text(), do.lineEditErkennungstext.text(), int(do.lineEditErkennungsspalte.text()), int(do.lineEditErgebnisspalte.text()), do.checkBoxEindeutigkeitErzwingen.isChecked(), int(do.labelNtesVorkommen.text().split(".")[0]), do.lineEditTestIdent.text(), do.lineEditTestBezeichnung.text(), do.lineEditTestEinheit.text(), self.templateRootElement, do.angepassteErgebnisseDict)
                        if optimierungsId == "" or duplizieren: # Neue zeile
                            self.templateRootElement.append(optimierungElement.getXml())
                        else: # Zeile bearbeiten
                            class_optimierung.Optimierung.replaceOptimierungElement(self.templateRootElement, optimierungsId, optimierungElement.getXml())
                        try:
                            exceptions = self.gdtDateiOptimiert.applyTemplate(self.templateRootElement, vorschau=True)
                            if len(exceptions) == 0:
                                self.setStatusMessage("Test aus 6228 erstellt")
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
                            testuebernahme = dialogOptimierungBefundAusTest.Testuebernahme(platzhalterName, platzhalterFeldkennung, eindeutigkeitskriterien.copy())
                            testuebernahmen.append(testuebernahme)
                        befundElement = optimierungElement.find("befund")
                        befundzeile = str(befundElement.text) # type: ignore
                        break
            if self.treeWidgetOriginal.topLevelItemCount() > 0:
                do = dialogOptimierungBefundAusTest.OptimierungBefundAusTest(self.gdtDateiOptimiert, self.maxeindeutigkeitskriterien, testuebernahmen, befundzeile, self.templateRootElement)
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
            einzufuegendesZeichen = class_Enums.EinzufuegendeZeichen.Kein_Zeichen
            # Optimierungselement finden, wenn bereits vorhanden (bearbeiten)
            if optimierungsId != "":
                for optimierungElement in self.templateRootElement.findall("optimierung"):
                    if str(optimierungElement.get("id")) == optimierungsId:
                        feldkennung = str(optimierungElement.find("feldkennung").text) # type:ignore
                        # Ab 2.9.0
                        if optimierungElement.find("einzufuegendeszeichen") != None:
                            einzufuegendesZeichen = class_Enums.EinzufuegendeZeichen[str(optimierungElement.find("einzufuegendeszeichen").text)] # type: ignore
                        break
            if self.treeWidgetOriginal.topLevelItemCount() > 0:
                do = dialogOptimierungConcatInhalte.OptimierungConcatInhalte(feldkennung, einzufuegendesZeichen)
                if do.exec() == 1:
                    self.templateRootDefinieren()
                    optimierungElement = class_optimierung.OptiConcatInhalte(do.lineEditFeldkennung.text(), class_Enums.EinzufuegendeZeichen[do.comboBoxZeichenEinfuegen.currentText().replace(" ", "_")], self.templateRootElement)
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

    def optimierenMenuPdfHinzufuegen(self, checked, optimierungsId:str=""):
        if self.addOnsFreigeschaltet:
            originalpfad = ""
            originalname = ""
            speichername = ""
            dateiformat = "PDF"
            # Optimierungselement finden, wenn bereits vorhanden (bearbeiten)
            if optimierungsId != "":
                for optimierungElement in self.templateRootElement.findall("optimierung"):
                    if str(optimierungElement.get("id")) == optimierungsId:
                        originalpfad = str(optimierungElement.find("originalpfad").text) # type:ignore
                        originalname = str(optimierungElement.find("originalname").text) # type:ignore
                        speichername = str(optimierungElement.find("speichername").text) # type:ignore
                        # Ab Version 2.5.0
                        if optimierungElement.find("dateiformat") != None:
                            dateiformat = str(optimierungElement.find("dateiformat").text) # type:ignore
                        break
            if self.treeWidgetOriginal.topLevelItemCount() > 0:
                do = dialogOptimierungAddPdf.OptimierungAddPdf(self.gdtDateiOriginal, originalpfad, originalname, speichername, dateiformat)
                if do.exec() == 1:
                    self.templateRootDefinieren()
                    optimierungElement = class_optimierung.OptiAddPdf(do.lineEditVerzeichnis.text(), do.lineEditName.text(), do.lineEditNameUebertragen.text(), do.lineEditDateiformat.text().upper(), self.templateRootElement)
                    if optimierungsId == "": # Neue zeile
                        self.templateRootElement.append(optimierungElement.getXml())
                    else: # Zeile bearbeiten
                        class_optimierung.Optimierung.replaceOptimierungElement(self.templateRootElement, optimierungsId, optimierungElement.getXml())
                    try:
                        exceptions = self.gdtDateiOptimiert.applyTemplate(self.templateRootElement, vorschau=True)
                        if len(exceptions) == 0:
                            self.setStatusMessage("PDF-Datei hinzugefügt")
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
                
    def optimierenMenuVerzeichnisueberwachungStarten(self):
        self.pushButtonUeberwachungStartenClicked(True)
        
    def optimierenMenuInDenHintergrund(self):
        self.setWindowState(Qt.WindowState.WindowNoState)
        self.setHidden(True)
        self.trayMenuZeigenAction.setEnabled(True)
        self.trayMenuUeberwachungNeuStartenAction.setEnabled(True)

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
                self.optimierenMenuTestAus6228(False, False, optimierungsId)
            elif optimierungstyp == "befundAusTest":
                self.optimierenMenuBefundAusTest(False, optimierungsId)
            elif optimierungstyp == "concatInhalte":
                self.optimierenMenuInhalteZusammenfuehren(False, optimierungsId)
            elif optimierungstyp == "addPdf":
                self.optimierenMenuPdfHinzufuegen(False, optimierungsId)
            self.setStatusMessage("Optimierung bearbeitet")
        except class_gdtdatei.GdtFehlerException as e:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Fehler beim Bebrbeiten der Optimierung: " + e.meldung, QMessageBox.StandardButton.Ok)
            mb.exec()

    def optimierungDuplizieren(self):
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
                self.optimierenMenuTestAus6228(False, True, optimierungsId)
            elif optimierungstyp == "befundAusTest":
                self.optimierenMenuBefundAusTest(False, optimierungsId)
            elif optimierungstyp == "concatInhalte":
                self.optimierenMenuInhalteZusammenfuehren(False, optimierungsId)
            elif optimierungstyp == "addPdf":
                self.optimierenMenuPdfHinzufuegen(False, optimierungsId)
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
            optimierungEntfernen = True
            testIdentWirdVerwendet = False
            verwendeteOptimierungsId = ""
            verwendeterBefundtext = ""
            if class_optimierung.Optimierung.getTypVonId(self.templateRootElement, optimierungsId) == "testAus6228":
                testIdent = str(self.templateRootElement.findtext("optimierung[@id='" + optimierungsId + "']/testIdent"))
                for optimierungElement in self.templateRootElement.findall("optimierung[@typ='befundAusTest']"):
                    verwendeteOptimierungsId = str(optimierungElement.get("id"))
                    verwendeterBefundtext = str(optimierungElement.findtext("befund"))
                    for kriteriumElement in optimierungElement.findall("test/eindeutigkeitskriterien/kriterium"):
                        if testIdent == str(kriteriumElement.text):
                            testIdentWirdVerwendet = True
                            break
                if testIdentWirdVerwendet:
                    mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Der Test-Ident \"" + testIdent + "\" wird als Eindeutigkeitskriterium in einem Befundtext verwendet. Sollen die ausgewählte Optimierung dennoch entfernt werden? Der davon abhängige Befundtext \"" + verwendeterBefundtext + "\" wird dadurch ebenfalls entfernt.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    mb.setDefaultButton(QMessageBox.StandardButton.No)
                    mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                    mb.button(QMessageBox.StandardButton.No).setText("Nein")
                    if mb.exec() == QMessageBox.StandardButton.No:
                        optimierungEntfernen = False
            if optimierungEntfernen:
                try:
                    class_optimierung.Optimierung.removeOptimierungElement(self.templateRootElement, optimierungsId)
                    if testIdentWirdVerwendet:
                        class_optimierung.Optimierung.removeOptimierungElement(self.templateRootElement, verwendeteOptimierungsId)
                    self.gdtDateiOptimiert.applyTemplate(self.templateRootElement, vorschau=True)
                    self.treeWidgetAusfuellen(self.treeWidgetOptimiert, self.gdtDateiOptimiert)
                    self.setStatusMessage("Optimierung entfernt")
                    self.ungesichertesTemplate = True
                except class_gdtdatei.GdtFehlerException as e:
                    mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Fehler beim Entfernen der Optimierung: " + e.meldung, QMessageBox.StandardButton.Ok)
                    mb.exec()

    def pushButtonUeberwachungStartenClicked(self, checked):
        if self.addOnsFreigeschaltet:
            fortfahren = True
            if self.ungesichertesTemplate and checked:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Beim Starten der Verzeichnisübrerwachung gehen derzeit nicht gesicherte Daten verloren.\nWollen Sie dennoch fortfahren?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.No)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.No:
                    fortfahren = False
            if fortfahren:
                if self.importWorker == None:
                    logger.logger.info("Bisher kein ImportWorker instanziert")
                    self.importWorker = class_importWorker.ImportWorker(self.gdtImportVerzeichnisSekundaer)
                    logger.logger.info("ImportWorker instanziert")
                    self.importWorker.signals.importVerzeichnisGefunden.connect(self.importVerzeichnisGefunden)
                    self.importWorker.signals.importWorkerRunning.connect(self.importWorkerRunning)
                    logger.logger.info("ImportWorker-Signale verbunden")
                if checked:
                    self.ungesichertesTemplate = False
                    logger.logger.info("Verzeichnungsüberwachungsbutton checked")
                    if os.path.exists(self.gdtImportVerzeichnis):
                        # Importverzeichnis auf nicht bearbeitete GDT-Dateien prüfen
                        gdtDateien = []
                        for importordnerFile in os.listdir(self.gdtImportVerzeichnis):
                            if re.match(reGdtDateiendung, importordnerFile[-4:].lower()) != None:
                                logger.logger.info(importordnerFile + " in Importverzeichnis " + self.gdtImportVerzeichnis + " gefunden")
                                gdtDateien.append(importordnerFile)
                        if len(gdtDateien) > 0:
                            mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Es sind noch nicht bearbeitete GDT-Dateien im primären Importverzeichnis. Sollen diese jetzt bearbeitet werden?\nDurch Klick auf \"Nein\" werden die Dateien gelöscht.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                            mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                            mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                            mb.button(QMessageBox.StandardButton.No).setText("Nein")
                            if mb.exec() == QMessageBox.StandardButton.Yes:
                                self.directoryChanged(self.gdtImportVerzeichnis)
                            else:
                                for gdtDatei in gdtDateien:
                                    os.unlink(os.path.join(self.gdtImportVerzeichnis, gdtDatei))
                        if self.sekundaeresimportverzeichnispruefen:
                            self.threadPool.start(self.importWorker)
                            logger.logger.info("ImportWorker gestartet")
                        if os.path.exists(self.gdtImportVerzeichnisSekundaer):
                            gdtDateien.clear()
                            for importordnerFile in os.listdir(self.gdtImportVerzeichnisSekundaer):
                                if re.match(reGdtDateiendung, importordnerFile[-4:].lower()) != None:
                                    logger.logger.info(importordnerFile + " in Importverzeichnis " + self.gdtImportVerzeichnisSekundaer + " gefunden")
                                    gdtDateien.append(importordnerFile)
                            if len(gdtDateien) > 0:
                                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Es sind noch nicht bearbeitete GDT-Dateien im sekundären Importverzeichnis. Sollen diese jetzt bearbeitet werden?\nDurch Klick auf \"Nein\" werden die Dateien gelöscht.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                                if mb.exec() == QMessageBox.StandardButton.Yes:
                                    self.directoryChanged(self.gdtImportVerzeichnisSekundaer)
                                else:
                                    for gdtDatei in gdtDateien:
                                        os.unlink(os.path.join(self.gdtImportVerzeichnisSekundaer, gdtDatei))
                        self.tray.showMessage("OptiGDT", "Überwachung gestartet")
                        self.tray.setToolTip("OptiGDT-Überwachung aktiv")
                        logger.logger.info("FileSystemWatcher instanziert")
                        verzeichnisse = [self.gdtImportVerzeichnis]
                        if os.path.exists(self.gdtImportVerzeichnisSekundaer):
                            verzeichnisse.append(self.gdtImportVerzeichnisSekundaer)
                        fsw.addPaths(verzeichnisse)
                        logger.logger.info("Importverzeichnis(se) " + str.join(", ", verzeichnisse) + " dem Watcher hinzugefügt")
                        fsw.directoryChanged.connect(self.directoryChanged)
                        logger.logger.info("Methode directoryChanged verbunden")
                        self.pushButtonUeberwachungStarten.setText("Verzeichnisüberwachung anhalten")
                        self.pushButtonUeberwachungStarten.setStyleSheet("background:rgb(50,150,50);color:rgb(255,255,255);border:2px solid rgb(0,0,0)")
                        self.setStatusMessage("Verzeichnisüberwachung gestartet")
                        self.trayMenuZeigenAction.setEnabled(True)
                        self.trayMenuUeberwachungNeuStartenAction.setEnabled(True)
                        self.ueberwachungAktiv = True
                        self.labelTreeViewUeberschriftLinks.setText("")
                        self.labelTreeViewUeberschriftRechts.setText("")
                        self.treeWidgetOriginal.clear()
                        self.treeWidgetOptimiert.clear()
                        self.lineEditName.setText("")
                        self.lineEditKennfeld.setText("")
                        self.lineEditGdtId.setText("")
                        self.lineEditGdtDateiname.setText("")
                        self.checkboxImmerGdtAlsExportDateiendung.setChecked(False)
                        self.lineEditExportverzeichnis.setText("")
                        self.checkBoxKennfeld.setChecked(False)
                        self.checkBoxGdtId.setChecked(False)
                        self.ungesichertesTemplate = False
                        if not self.isHidden():
                            self.setWindowState(Qt.WindowState.WindowNoState)
                            self.setHidden(True)
                    else:
                        mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Das Importverzeichnis \"" + self.gdtImportVerzeichnis + "\" existiert nicht.", QMessageBox.StandardButton.Ok)
                        mb.exec()
                else:
                    logger.logger.info("Verzeichnungsüberwachungsbutton not checked")
                    if self.sekundaeresimportverzeichnispruefen:
                        self.importWorker.kill()
                    self.pushButtonUeberwachungStarten.setStyleSheet("background:rgb(0,50,0);color:rgb(255,255,255);border:2px solid rgb(0,0,0)")
                    self.pushButtonUeberwachungStarten.setText("Verzeichnisüberwachung starten")
                    fsw.removePath(self.gdtImportVerzeichnis)
                    if self.gdtImportVerzeichnisSekundaer in fsw.directories():
                        fsw.removePath(self.gdtImportVerzeichnisSekundaer)
                    logger.logger.info("Importverzeichnis " + self.gdtImportVerzeichnis + " vom Watcher entfernt")
                    self.tray.showMessage("OptiGDT", "Überwachung angehalten")
                    self.setStatusMessage("Verzeichnisüberwachung angehalten")
                    self.tray.setToolTip("OptiGDT-Überwachung inaktiv")
                    self.optimierenMenuVerzeichnisueberwachungStartenAction.setEnabled(True)
                    self.optimierenMenuInDenHintergrundAction.setEnabled(False)
                    self.ueberwachungAktiv = False
        else:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Für diese Funktion ist eine gültige Lizenz notwendig.", QMessageBox.StandardButton.Ok)
            mb.exec()

    def importVerzeichnisGefunden(self, gefunden):
        if gefunden:
            logger.logger.info("Sekundärer Importpfad " + self.gdtImportVerzeichnisSekundaer + " gefunden")
            fsw.addPath(self.gdtImportVerzeichnisSekundaer)
            dir = fsw.directories()
            logger.logger.info("Überwacht: " + str.join(", ", dir))
        else:
            logger.logger.info("Sekundärer Importpfad " + self.gdtImportVerzeichnisSekundaer + " nicht gefunden")

    def importWorkerRunning(self, running):
        if running:
            logger.logger.info("ImportWorker gestartet")
        else:
            logger.logger.info("ImportWorker gestoppt")

    def deleteImportverzeichnis(self):
        for file in os.listdir(self.gdtImportVerzeichnis):
            os.unlink(file)

    def directoryChanged(self, changeVerzeichnis):
        """
        Durchsucht das Verzeichnis nach .gdt- und .001-.999-Dateien, wendet das entsprechrende Template an, speichert die Datei im Exportverzeichnis unter dem gleichen Namen und löscht die importierte Datei
        """
        time.sleep(self.sekundenBisTemplatebearbeitung)
        logger.logger.info("Innerhalb directoryChanged")
        files = []
        if os.path.exists(changeVerzeichnis):
            files = os.listdir(changeVerzeichnis)
        for gdtDateiname in files:
            logger.logger.info("Name in files: " + gdtDateiname)
            if len(gdtDateiname) > 4:
                dateiendung = gdtDateiname[-4:]
                if re.match(reGdtDateiendung, dateiendung.lower()) != None:
                    logger.logger.info("GDT-Datei " + gdtDateiname + " gefunden")
                    gd = class_gdtdatei.GdtDatei(class_gdtdatei.GdtZeichensatz.IBM_CP437)
                    gd.laden(os.path.join(changeVerzeichnis, gdtDateiname))
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
                        gd.laden(os.path.join(changeVerzeichnis, gdtDateiname))
                        logger.logger.info("GDT-Datei " + os.path.join(changeVerzeichnis, gdtDateiname) + " mit Zeichensatz " + str(class_gdtdatei.GdtZeichensatz(zeichensatz)) + " geladen")
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
                            immerGdtAlsExportDateiendung = class_gdtdatei.GdtDatei.getTemplateInfo(os.path.join(self.standardTemplateVerzeichnis, templateDateiname))[4]
                            kennfeldKorrekt = True
                            if kennfeldTemplate != "":
                                kennfeldKorrekt = kennfeldGdtDatei == kennfeldTemplate
                            gdtIdKorrekt = True
                            if gdtIdTemplate != "":
                                gdtIdKorrekt = gdtIdGdtDatei == gdtIdTemplate
                            logger.logger.info("Vorhandenes Template: " + os.path.join(self.standardTemplateVerzeichnis, templateDateiname))
                            gdtDateinameKorrekt = False
                            if dateiendung.lower() == ".gdt":
                                gdtDateinameKorrekt = gdtDateinameInTemplate == gdtDateiname
                            elif re.match(reGdtDateiendungSequentiell, dateiendung) != None:
                                gdtDateinameKorrekt = re.match(reGdtDateiendungSequentiell, gdtDateinameInTemplate[-4:]) and gdtDateinameInTemplate[:-4] == gdtDateiname[:-4]
                            if gdtDateinameKorrekt and kennfeldKorrekt and gdtIdKorrekt:
                                templateGefunden = True
                                logger.logger.info("Zu " + gdtDateiname + " passendendes Template " + os.path.join(self.standardTemplateVerzeichnis, templateDateiname) + " gefunden")
                                try:
                                    exceptions = gd.applyTemplateVonPfad(os.path.join(self.standardTemplateVerzeichnis, templateDateiname))
                                    logger.logger.info(os.path.join(self.standardTemplateVerzeichnis, templateDateiname) + " angewendet")
                                    if len(exceptions) > 0:
                                        exceptionListe = ", ".join(exceptions)
                                        logger.logger.warning("Fehlerliste nach Templateanwendung: " + exceptionListe)
                                    ## Auf gesetzte Zeilenumbrüche prüfen
                                    try:
                                        erster6220Inhalt = gd.getInhalte("6220")[0]
                                        befundzeilen = []
                                        if "//" in erster6220Inhalt:
                                            for befundzeile in erster6220Inhalt.split("//"):
                                                befundzeilen.append(befundzeile)
                                        else:
                                            befundzeilen.append(erster6220Inhalt)
                                        gd.deleteZeile("", "6220")
                                        for zeile in befundzeilen:
                                            zeileMitKommas = zeile
                                            # Dezimalpunkt in Komma wandeln
                                            if self.punktinkomma6220:
                                                regexPattern = r"-?\d+\.\d+"
                                                dezimalpunktzahlen = re.findall(regexPattern, zeile)
                                                for dezimalpunktzahl in dezimalpunktzahlen:
                                                    dezimalkommazahl = dezimalpunktzahl.replace(".", ",")
                                                    zeileMitKommas = zeileMitKommas.replace(dezimalpunktzahl, dezimalkommazahl)
                                            gd.addZeile("6220", zeileMitKommas)
                                    except:
                                        pass
                                    gd.setSatzlaenge()
                                    ## Nur mit Lizenz
                                    if self.pseudoLizenzId != "":
                                        gd.changeZeile("", "3000", self.pseudoLizenzId)
                                    ## /Nur mit Lizenz
                                    if immerGdtAlsExportDateiendung:
                                        gdtDateiname = gdtDateiname[:-4] + ".gdt"
                                    with open(os.path.join(exportverzeichnis, gdtDateiname), "w", encoding=gd.getZeichensatzAlsPythonString(), newline="") as file:
                                        for zeile in gd.getZeilen():
                                            file.write(zeile + "\r\n")
                                    if immerGdtAlsExportDateiendung:
                                        logger.logger.info("Optimierte GDT-Datei " + gdtDateiname + " in " + exportverzeichnis + " gespeichert (Dateiendung von " + dateiendung + " in .gdt geändert)") 
                                    else:
                                        logger.logger.info("Optimierte GDT-Datei " + gdtDateiname + " in " + exportverzeichnis + " gespeichert") 
                                    os.unlink(os.path.join(changeVerzeichnis, gdtDateiname))
                                    logger.logger.info("Originale GDT-Datei " + gdtDateiname + " gelöscht")
                                    self.tray.showMessage("OptiGDT", "Template \"" + templateDateiname[:-4] + "\" angewendet")
                                    break
                                except IOError as e:
                                    logger.logger.error("IO-Error beim Speichern der optimierten GDT-Datei "+ gdtDateiname + " in " + exportverzeichnis)
                                except class_optimierung.OptimierungsfehlerException as e:
                                    logger.logger.warning("OptimierungsfehlerException bei Templateanwendung: " + e.meldung)
                    if not templateGefunden:
                        logger.logger.warning("Template für GDT-Datei " + gdtDateiname + " nicht gefunden")
                        raise class_optimierung.OptimierungsfehlerException("Template für GDT-Datei " + gdtDateiname + " nicht gefunden")
            else:
                logger.logger.info("Dateiname zu kurz: " + gdtDateiname)   

    def trayMenuZeigen(self):
        self.showNormal()
        self.trayMenuZeigenAction.setEnabled(False)
        self.trayMenuUeberwachungNeuStartenAction.setEnabled(False)
        if self.ueberwachungAktiv:
            self.optimierenMenuVerzeichnisueberwachungStartenAction.setEnabled(False)
            self.optimierenMenuInDenHintergrundAction.setEnabled(True)

    def trayMenuUeberwachungNeuStarten(self):
        pfadEntfernt = fsw.removePath(self.gdtImportVerzeichnis)
        if self.gdtImportVerzeichnisSekundaer in fsw.directories():
            pfadEntfernt = pfadEntfernt and fsw.removePath(self.gdtImportVerzeichnisSekundaer)
        time.sleep(2)
        verzeichnisse = [self.gdtImportVerzeichnis]
        if os.path.exists(self.gdtImportVerzeichnisSekundaer):
            verzeichnisse.append(self.gdtImportVerzeichnisSekundaer)
        pfadHinzugefügt = len(fsw.addPaths(verzeichnisse)) == 0
        if pfadEntfernt and pfadHinzugefügt:
            logger.logger.info("Überwachung für Importverzeichnis(se) " + str.join(", ", verzeichnisse) + " neu gestartet")
            self.tray.showMessage("OptiGDT", "Überwachung neu gestartet")
            self.directoryChanged(self.gdtImportVerzeichnis)
            self.directoryChanged(self.gdtImportVerzeichnisSekundaer)
        else:
            logger.logger.warning("Problem beim Neustart der Überwachung für Importverzeichnis(se) " + str.join(", ", verzeichnisse) + " neu gestartet")


    def trayMenuBeenden(self):
        if self.ueberwachungAktiv:
            mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Die GDT-Verzeichnisübrewachung ist aktiv.\nSoll OptiGDT dennoch beendet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, self)
            mb.setDefaultButton(QMessageBox.StandardButton.No)
            mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
            mb.button(QMessageBox.StandardButton.No).setText("Nein")
            if mb.exec() == QMessageBox.StandardButton.Yes:
                sys.exit()
        else:
            sys.exit()
    
    # Statische Methoden
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
app.setWindowIcon(QIcon(os.path.join(basedir, "icons", "program.png")))
window = MainWindow()
if not "ue" in sys.argv:
    window.show()
app.exec()