from PySide6.QtCore import QFileSystemWatcher
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
import sys, os, logger, time
import class_gdtdatei

basedir = os.path.dirname(__file__)

class FileSystemWatcher():
    def __init__(self, app, importverzeichnis:str, templateverzeichnis:str, sleepNachChange=3):
        """
        Instanziert eine OptiGDT Verzeichnis-Überwachung
        Parameter:
            importverzeichnis:str
            templateverzeichnis:str Verzeichnis, in dem sich die Templates befinden
            sleepNachChange:float Wartezeit nach Änderung im überwachten Verzeichnis bis zur Bearbeitung in Sekunden
        """
        tray = QSystemTrayIcon(app)
        iconpfad = os.path.join(basedir, "icons/program.png")
        icon = QIcon(iconpfad)
        tray.setIcon(icon)
        tray.setToolTip("OptiGDT-Überwachung aktiv")
        trayMenu = QMenu()
        trayMenuAction = QAction("OptiGDT beenden", app)
        trayMenu.addAction(trayMenuAction)
        trayMenuAction.triggered.connect(sys.exit) # type: ignore
        tray.setContextMenu(trayMenu)
        tray.show()
        self.importverzeichnis = importverzeichnis
        self.templateverzeichnis = templateverzeichnis
        self.sleepNachChange = sleepNachChange
        fsw = QFileSystemWatcher()
        logger.logger.info("FileSystemWatcher instanziert")
        fsw.addPath("/Users/fabian/Documents/import")
        logger.logger.info("Importverzeichnis " + importverzeichnis + " hinzugefügt")
        fsw.directoryChanged.connect(self.directoryChanged) # type: ignore
        logger.logger.info("Methode directoryChanged verbunden")

    def deleteImportverzeichnis(self):
        for file in os.listdir(self.importverzeichnis):
            os.unlink(file)

    def directoryChanged(self):
        """
        Durchsucht das Verzeichnis nach .gdt-Dateien, wendet das entsprechrende Template an, speichert die Datei im Exportverzeichnis unter dem gleichen Namen und löscht die importierte Datei
        """
        time.sleep(self.sleepNachChange)
        logger.logger.info("Innerhalb directoryChanged")
        files = os.listdir(self.importverzeichnis)
        for gdtDateiname in files:
            logger.logger.info("Name in files: " + gdtDateiname)
            if len(gdtDateiname) > 4:
                dateiendung = gdtDateiname[-4:]
                if dateiendung == ".gdt":
                    logger.logger.info("GDT-Datei " + gdtDateiname + " gefunden")
                    gd = class_gdtdatei.GdtDatei(class_gdtdatei.GdtZeichensatz.IBM_CP437)
                    gd.laden(os.path.join(self.importverzeichnis, gdtDateiname))
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
                    files = os.listdir(self.templateverzeichnis)
                    templateGefunden = False
                    for templateDateiname in files:
                        if templateDateiname[-4:] == ".ogt":
                            kennfeldTemplate = class_gdtdatei.GdtDatei.getTemplateInfo(os.path.join(self.templateverzeichnis, templateDateiname))[0]
                            gdtIdTemplate = class_gdtdatei.GdtDatei.getTemplateInfo(os.path.join(self.templateverzeichnis, templateDateiname))[1]
                            gdtDateinameInTemplate = class_gdtdatei.GdtDatei.getTemplateInfo(os.path.join(self.templateverzeichnis, templateDateiname))[2]
                            exportverzeichnis = class_gdtdatei.GdtDatei.getTemplateInfo(os.path.join(self.templateverzeichnis, templateDateiname))[3]
                            kennfeldKorrekt = kennfeldGdtDatei == kennfeldTemplate
                            gdtIdKorrekt = gdtIdGdtDatei == gdtIdTemplate
                            logger.logger.info("Vorhandenes Template: " + os.path.join(self.templateverzeichnis, templateDateiname))
                            if gdtDateinameInTemplate == gdtDateiname and kennfeldKorrekt and gdtIdKorrekt:
                                templateGefunden = True
                                logger.logger.info("Zu " + gdtDateiname + " passendendes Template " + os.path.join(self.templateverzeichnis, templateDateiname) + " gefunden")
                                try:
                                    exceptions = gd.applyTemplateVonPfad(os.path.join(self.templateverzeichnis, templateDateiname))
                                    if len(exceptions) == 0:
                                        logger.logger.info(os.path.join(self.templateverzeichnis, templateDateiname) + " angewendet")
                                        with open(os.path.join(exportverzeichnis, gdtDateiname), "w") as file:
                                            for zeile in gd.getZeilen():
                                                file.write(zeile + "\r\n")
                                        logger.logger.info("Optimierte GDT-Datei " + gdtDateiname + " gespeichert") 
                                        os.unlink(os.path.join(self.importverzeichnis, gdtDateiname))
                                        logger.logger.info("Originale GDT-Datei " + gdtDateiname + " gelöscht")
                                        break
                                    else:
                                        exceptionListe = ",".join(exceptions)
                                        logger.logger.error("Fehlerliste nach Templateanwendung: " + exceptionListe)
                                except OptimierungsfehlerException as e:
                                    logger.logger.warning("Exception in class_filesystemwatcher bei Templateanwendung: " + e.meldung)
                    if not templateGefunden:
                        logger.logger.warning("Template für GDT-Datei " + gdtDateiname + " nicht gefunden")
                        raise OptimierungsfehlerException("Template für GDT-Datei " + gdtDateiname + " nicht gefunden")
            else:
                logger.logger.info("Dateiname zu kurz: " + gdtDateiname)        

if __name__ == "__main__:":
    app = QApplication(sys.argv)
    if len(sys.argv) > 1:
        importVerzeichnis, templateverzeichnis = sys.argv[1], sys.argv[2]
    else:
        importVerzeichnis = "/Users/fabian/Documents/gdt"
        templateverzeichnis = "/Users/fabian/Documents/templates"
        # fs = FileSystemWatcher(importVerzeichnis, templateverzeichnis)
    app.exec()