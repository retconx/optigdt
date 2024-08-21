from PySide6.QtCore import QRunnable, Signal, Slot, QObject
import os, time

basedir = os.path.dirname(__file__)
    
class WorkerSignals(QObject):
    importVerzeichnisGefunden = Signal(bool)
    importWorkerRunning = Signal(bool)

class ImportWorker(QRunnable):

    def __init__(self, importVerzeichnis:str):
        super().__init__()
        self.signals = WorkerSignals()
        self.importVerzeichnis = importVerzeichnis
        self.is_killed = False

    def kill(self):
        self.is_killed = True
    
    @Slot()
    def run(self):
        self.signals.importWorkerRunning.emit(True)
        while not self.is_killed:
            if os.path.exists(self.importVerzeichnis):
                self.signals.importVerzeichnisGefunden.emit(True)
            else:
                self.signals.importVerzeichnisGefunden.emit(False)
            time.sleep(3)
        self.signals.importWorkerRunning.emit(False)

    
