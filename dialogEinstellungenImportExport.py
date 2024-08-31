import configparser, os, sys, datetime, zipfile
## Nur mit Lizenz
import gdttoolsL
## /import
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QGroupBox,
    QCheckBox,
    QFileDialog,
    QRadioButton,
    QMessageBox
)

class EinstellungenImportExport(QDialog):
    def __init__(self, configPath):
        super().__init__()
        self.setFixedWidth(360)
        self.configPath = configPath

        #config.ini lesen
        self.configIni = configparser.ConfigParser()
        self.configIni.read(os.path.join(configPath, "config.ini"))

        self.setWindowTitle("Einstellungen im-/ exportieren")
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setText("Importieren...")
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        ## Nur mit Lizenz# Prüfen, ob Lizenzschlüssel verschlüsselt in config.ini
        lizenzschluessel = self.configIni["Erweiterungen"]["lizenzschluessel"]
        if len(lizenzschluessel) != 29:
            lizenzschluessel = gdttoolsL.GdtToolsLizenzschluessel.dekrypt(lizenzschluessel)
        ## /Nur mit Lizenz

        mainLayoutV = QVBoxLayout()
        
        # Groupbox Import/Export
        groupboxImportExport = QGroupBox("Import/Export")
        groupboxImportExport.setStyleSheet("font-weight:bold")
        self.radiobuttonImport = QRadioButton()
        self.radiobuttonImport.setText("Importieren")
        self.radiobuttonImport.setStyleSheet("font-weight:normal")
        self.radiobuttonImport.setChecked(True)
        self.radiobuttonImport.clicked.connect(self.radiobuttonClicked)
        self.radiobuttonExport = QRadioButton()
        self.radiobuttonExport.setText("Exportieren")
        self.radiobuttonExport.setStyleSheet("font-weight:normal")
        self.radiobuttonExport.clicked.connect(self.radiobuttonClicked)
        groupboxImportExportLayout = QVBoxLayout()
        groupboxImportExportLayout.addWidget(self.radiobuttonImport)
        groupboxImportExportLayout.addWidget(self.radiobuttonExport)
        groupboxImportExport.setLayout(groupboxImportExportLayout)

        # Groupbox Einstellungen
        self.checkboxTextListe = ["Allgemeine Einstellungen", "Optimierungs-Einstellungen", "GDT-Einstellungen", "LANR/Lizenzschlüssel"]
        self.checkboxEinstellungen = []
        self.groupboxEinstellungen = QGroupBox("Zu exportierende Einstellungen")
        self.groupboxEinstellungen.setStyleSheet("font-weight:bold")
        for text in self.checkboxTextListe:
            tempCheckbox = QCheckBox(text)
            tempCheckbox.setStyleSheet("font-weight:normal")
            tempCheckbox.setChecked(True)
            tempCheckbox.clicked.connect(self.checkboxClicked)
            self.checkboxEinstellungen.append(tempCheckbox)
        self.checkboxEinstellungen[0].setEnabled(False)
        groupboxEinstellungenLayout = QVBoxLayout()
        for cb in self.checkboxEinstellungen:
            groupboxEinstellungenLayout.addWidget(cb)
        self.groupboxEinstellungen.setLayout(groupboxEinstellungenLayout)

        self.checkBoxReferenzGdtDateiverzeichnisEinbeziehen = QCheckBox("Referenz-GDT-Dateiverzeichnis einbeziehen")
        self.checkBoxReferenzGdtDateiverzeichnisEinbeziehen.setStyleSheet("font-weight:normal")
        self.checkBoxReferenzGdtDateiverzeichnisEinbeziehen.setChecked(True)
        
        mainLayoutV.addWidget(groupboxImportExport)
        mainLayoutV.addWidget(self.groupboxEinstellungen)
        mainLayoutV.addWidget(self.checkBoxReferenzGdtDateiverzeichnisEinbeziehen)
        mainLayoutV.addWidget(self.buttonBox)
        self.setLayout(mainLayoutV)
        self.radiobuttonClicked()

    def radiobuttonClicked(self):
        if self.radiobuttonImport.isChecked():
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setText("Importieren...")
            self.groupboxEinstellungen.setTitle("Zu importierende Einstellungen")
            self.checkBoxReferenzGdtDateiverzeichnisEinbeziehen.setEnabled(True)
            self.checkBoxReferenzGdtDateiverzeichnisEinbeziehen.setChecked(True)
        else:
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setText("Exportieren...")
            self.groupboxEinstellungen.setTitle("Zu exportierende Einstellungen")
            self.checkBoxReferenzGdtDateiverzeichnisEinbeziehen.setEnabled(os.path.exists(os.path.join(self.configPath, "gdtreferenzen")))
            self.checkBoxReferenzGdtDateiverzeichnisEinbeziehen.setChecked(os.path.exists(os.path.join(self.configPath, "gdtreferenzen")))

    def checkboxClicked(self):
        gecheckt = 0
        for cb in self.checkboxEinstellungen:
            if cb.isChecked():
                gecheckt += 1
        if gecheckt == 0:
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        else:
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)



    def accept(self):
        if self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).text() == "Importieren...":
            fd = QFileDialog(self)
            fd.setFileMode(QFileDialog.FileMode.ExistingFile)
            fd.setWindowTitle("Einstellungen importieren")
            fd.setModal(True)
            fd.setNameFilters(["OptiGDT-Einstellungsdateien (*.oed *.zip)"])
            fd.setLabelText(QFileDialog.DialogLabel.Accept, "Laden")
            fd.setLabelText(QFileDialog.DialogLabel.Reject, "Abbrechen")
            if fd.exec() == 1:
                ausgewaehlteDatei = fd.selectedFiles()[0]
                configImport = configparser.ConfigParser()
                configPfad = ausgewaehlteDatei
                if ausgewaehlteDatei[-3:] == "zip":
                    zipfilePfad = ausgewaehlteDatei
                    zf = zipfile.ZipFile(zipfilePfad, "r")
                    zf.extract("config.ini", self.configPath)
                    configPfad = os.path.join(self.configPath, "config.ini")          
                configImport.read(configPfad)
                if "Allgemein" in configImport.sections() or "Optimierung" in configImport.sections() or "GDT" in configImport.sections() or "Erweiterungen" in configImport.sections():
                    i=0
                    for section in configImport.sections():
                        if self.checkboxEinstellungen[i].isChecked():
                            for option in configImport.options(section):
                                self.configIni[section][option] = configImport.get(section, option)
                        i += 1
                    try:
                        with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                            self.configIni.write(configfile)
                        referenzdateienImportiert = ""
                        if self.checkBoxReferenzGdtDateiverzeichnisEinbeziehen.isChecked() and ausgewaehlteDatei[-3:] == "zip": # ab 2.8.2
                            try:
                                referenzGdtDateien = [rd for rd in zf.namelist() if rd.startswith("gdtreferenzen")]
                                for referenzGdtDatei in referenzGdtDateien:
                                    zf.extract(referenzGdtDatei, self.configPath)
                                referenzdateienImportiert = " sowie das Referenz-GDT-Dateiverzeichnis"
                            except:
                                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Fehler beim Entpacken der Referenz-GDT-Dateien", QMessageBox.StandardButton.Ok)
                                mb.exec()
                        self.done(1)
                        mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von OptiGDT", "Die Einstellungen" + referenzdateienImportiert +  " wurden erfolgreich importiert. Damit diese wirksam werden, muss OptiGDT neu gestartet werden.\nSoll OptiGDT neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                        mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                        mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                        mb.button(QMessageBox.StandardButton.No).setText("Nein")
                        if mb.exec() == QMessageBox.StandardButton.Yes:
                            os.execl(sys.executable, __file__, *sys.argv)
                    except Exception as e:
                        mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Fehler beim Importieren der Einstellungen: " + str(e), QMessageBox.StandardButton.Ok)
                        mb.exec()
                else:
                    mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Die Datei " + configPfad + " ist keine gültige OptiGDT-Konfigurationsdatei", QMessageBox.StandardButton.Ok)
                    mb.exec()
        else: # Exportieren...
            fd = QFileDialog(self)
            fd.setFileMode(QFileDialog.FileMode.Directory)
            fd.setWindowTitle("Einstellungen exportieren")
            fd.setModal(True)
            fd.setLabelText(QFileDialog.DialogLabel.Accept, "Speichern")
            fd.setLabelText(QFileDialog.DialogLabel.Reject, "Abbrechen")
            if fd.exec() == 1:
                configExport = configparser.ConfigParser()
                ausgewaehlterPfad = fd.directory().absolutePath()
                zeitstempelString = datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d%H%M%S")
                zipName = zeitstempelString + "_OptiGdtEinstellungen.zip"
                zipPfad = os.path.join(ausgewaehlterPfad, zipName)
                zf = zipfile.ZipFile(zipPfad, "w")
                configName = "config.ini"
                configPfad = os.path.join(ausgewaehlterPfad, configName)
                try:
                    with open(configPfad, "w") as exportfile:
                        if self.checkboxEinstellungen[0].isChecked():
                            section = "Allgemein"
                            configExport.add_section(section)
                            for option in self.configIni.options(section):
                                configExport[section][option] = self.configIni[section][option]
                        if self.checkboxEinstellungen[1].isChecked():
                            section = "Optimierung"
                            configExport.add_section(section)
                            for option in self.configIni.options(section):
                                configExport[section][option] = self.configIni[section][option]
                        if self.checkboxEinstellungen[2].isChecked():
                            section = "GDT"
                            configExport.add_section(section)
                            for option in self.configIni.options(section):
                                configExport[section][option] = self.configIni[section][option]
                        if self.checkboxEinstellungen[3].isChecked():
                            section = "Erweiterungen"
                            configExport.add_section(section)
                            for option in self.configIni.options(section):
                                configExport[section][option] = self.configIni[section][option]
                        configExport.write(exportfile)
                        exportfile.close()
                        zf.write(configPfad, configName)
                        os.unlink(configPfad)
                        # Referenz-GDT-Dateiverzeichnis zippen
                        referenzdateienExportiert = ""
                        if self.checkBoxReferenzGdtDateiverzeichnisEinbeziehen.isChecked():
                            try:
                                zf.mkdir("gdtreferenzen", mode=0o777)
                                for referenzdateiName in os.listdir(os.path.join(self.configPath, "gdtreferenzen")):
                                    referenzdateiPfad = os.path.join(self.configPath, "gdtreferenzen", referenzdateiName)
                                    if "_ref_" in referenzdateiName:
                                        zf.write(referenzdateiPfad, os.path.join("gdtreferenzen", referenzdateiName))
                                referenzdateienExportiert = " sowie das Referenz-GDT-Dateiverzeichnis"
                            except:
                                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Problem beim Komprimieren des Referenz-GDT-Dateiverzeichnisses", QMessageBox.StandardButton.Ok)
                                mb.exec()
                        mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von OptiGDT", "Die gewünschten Einstellungen" + referenzdateienExportiert + " wurden erfolgreich unter dem Namen " + zipName + " exportiert." + referenzdateienExportiert, QMessageBox.StandardButton.Ok)
                        mb.exec()
                        self.done(1)
                except Exception as e:
                    mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von OptiGDT", "Fehler beim Exportieren der Einstellungen: " + str(e), QMessageBox.StandardButton.Ok)
                    mb.exec()
                            
