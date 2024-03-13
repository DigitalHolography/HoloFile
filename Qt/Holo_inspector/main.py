import sys
import struct
import json
import os
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QTreeWidget, QTreeWidgetItem, QHeaderView

class HoloFileReader(QWidget):
    def __init__(self):
        super().__init__()
        self.jsonData = None  # Variable pour stocker les données JSON
        self.appVersion = "1.0"
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Holo file inspector (' + self.appVersion + ' ver)')
        self.setMinimumSize(600, 400)  # Définir une taille minimale pour la fenêtre
        self.layout = QVBoxLayout()

        self.openButton = QPushButton('Open Holo File')
        self.openButton.clicked.connect(self.openFileDialog)
        self.layout.addWidget(self.openButton)

        self.downloadJsonButton = QPushButton('Download JSON')
        self.downloadJsonButton.clicked.connect(self.downloadJson)
        self.downloadJsonButton.setEnabled(False)  # Désactiver le bouton jusqu'à ce que le JSON soit chargé
        self.layout.addWidget(self.downloadJsonButton)

        self.jsonView = QTreeWidget()
        self.jsonView.setHeaderLabels(["Key", "Value"])
        self.jsonView.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.layout.addWidget(self.jsonView)

        self.setLayout(self.layout)

    def openFileDialog(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Open Holo File", "", "All Files (*);;Holo Files (*.holo)", options=options)
        if fileName:
            self.readFile(fileName)

    def readFile(self, filePath):
        with open(filePath, 'rb') as file:
            header = file.read(64)  # Read the first 64 bytes
            self.unpackHeader(header, filePath)

    def unpackHeader(self, header, filePath):
        format_string1 = '4sHHIII'
        format_string2 = 'QB35x'
        data1 = struct.unpack(format_string1, header[:20])
        data2 = struct.unpack(format_string2, header[20:])
        data = data1 + data2
        magic_number, version, bits_per_pixel, img_width, img_height, img_nb, total_data_size, endianness = data

        magic_number = magic_number.decode('utf-8')
        footer = self.readFooter(filePath, total_data_size)

        self.jsonView.clear()  # Clear previous data
        # Ajouter des informations d'en-tête au QTreeWidget
        self.addItems(self.jsonView.invisibleRootItem(), {
            "Magic Number": magic_number,
            "Version": version,
            "Bits per Pixel": bits_per_pixel,
            "Image Width": img_width,
            "Image Height": img_height,
            "Image Number": img_nb,
            "Total Data Size": total_data_size,
            "Endianness": endianness
        })

        # Gérer l'affichage du footer s'il est présent
        if isinstance(footer, dict):
            self.addItems(self.jsonView.invisibleRootItem(), {"Footer": footer})
        else:
                # Si le footer n'existe pas ou est invalide, afficher un message et désactiver le bouton de téléchargement
                self.addItems(self.jsonView.invisibleRootItem(), {"Footer": "No footer found or it is invalid."})
                self.jsonData = None  # Réinitialiser les données JSON
                self.downloadJsonButton.setEnabled(False)  # Désactiver le bouton de téléchargement

    def readFooter(self, filePath, total_data_size):
        fileSize = os.path.getsize(filePath)
        if fileSize > total_data_size + 64:
            with open(filePath, 'rb') as file:
                file.seek(total_data_size + 64)
                footerJson = file.read().decode('utf-8')
                try:
                    footer = json.loads(footerJson)
                    self.jsonData = json.loads(footerJson)
                    self.downloadJsonButton.setEnabled(True)
                    return footer
                except json.JSONDecodeError:
                    return 'Invalid JSON footer.'
        return 'No footer found.'

    def downloadJson(self):
            if self.jsonData is not None:
                fileName, _ = QFileDialog.getSaveFileName(self, "Save JSON File", "", "JSON Files (*.json)")
                if fileName:
                    with open(fileName, 'w') as file:
                        json.dump(self.jsonData, file, indent=4)
                    self.downloadJsonButton.setEnabled(False)

    def addItems(self, parent, json_data):
        for key, value in json_data.items():
            if isinstance(value, dict) or isinstance(value, list):
                item = QTreeWidgetItem(parent, [key, ""])
                if isinstance(value, dict):
                    self.addItems(item, value)
                elif isinstance(value, list):
                    for val in value:
                        if isinstance(val, dict):
                            self.addItems(item, val)
                        else:
                            QTreeWidgetItem(item, ["", str(val)])
            else:
                QTreeWidgetItem(parent, [key, str(value)])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = HoloFileReader()
    ex.show()
    sys.exit(app.exec())
