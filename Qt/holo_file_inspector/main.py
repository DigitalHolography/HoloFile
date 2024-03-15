from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QTreeWidget, QTreeWidgetItem, QHeaderView, QPlainTextEdit
from PySide6.QtCore import Qt
import sys
import subprocess
import struct
import json
import os

class HoloFileReader(QWidget):
    def __init__(self):
        super().__init__()
        self.jsonData = None  # Variable pour stocker les données JSON
        self.file = ""
        self.data_size = 0
        self.appVersion = "1.3"
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Holo file inspector (' + self.appVersion + ' ver)')
        self.setMinimumSize(600, 400)  # Définir une taille minimale pour la fenêtre
        self.layout = QVBoxLayout()

        self.openButton = QPushButton('Open Holo File')
        self.openButton.clicked.connect(self.openFileDialog)
        self.layout.addWidget(self.openButton)

        self.overwriteFooterButton = QPushButton('Overwrite Footer')
        self.overwriteFooterButton.clicked.connect(self.overwriteFooter)
        self.overwriteFooterButton.setEnabled(False)  # Désactivé jusqu'à ce qu'un fichier soit chargé et modifié
        self.layout.addWidget(self.overwriteFooterButton)

        self.loadFooterButton = QPushButton('Load Footer')
        self.loadFooterButton.clicked.connect(self.loadFooter)
        self.loadFooterButton.setEnabled(False)
        self.layout.addWidget(self.loadFooterButton)

        self.downloadJsonButton = QPushButton('Download JSON')
        self.downloadJsonButton.clicked.connect(self.downloadJson)
        self.downloadJsonButton.setEnabled(False)  # Désactiver le bouton jusqu'à ce que le JSON soit chargé
        self.layout.addWidget(self.downloadJsonButton)

        self.jsonView = QTreeWidget()
        self.jsonView.setHeaderLabels(["Key", "Value"])
        self.jsonView.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.jsonView.itemDoubleClicked.connect(self.editItem)  # Connecter le double clic sur un élément à la méthode d'édition
        self.jsonView.itemChanged.connect(self.onItemChanged)
        self.layout.addWidget(self.jsonView)

        self.logWindow = QPlainTextEdit()
        self.logWindow.setReadOnly(True)  # Rendre le widget en lecture seule pour éviter la modification des logs
        self.logWindow.setMaximumHeight(100)  # Définir une hauteur maximale pour le widget de log
        self.layout.addWidget(self.logWindow)

        self.executeFileButton = QPushButton('Execute File')
        self.executeFileButton.clicked.connect(self.executeFile)
        self.executeFileButton.setEnabled(False)  # Désactiver le bouton jusqu'à ce qu'un fichier soit chargé
        self.layout.addWidget(self.executeFileButton)

        self.setLayout(self.layout)

    def openFileDialog(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Open Holo File", "", "All Files (*);;Holo Files (*.holo)", options=options)
        if fileName:
            self.readFile(fileName)

    def readFile(self, filePath):
        with open(filePath, 'rb') as file:
            header = file.read(64)  # Read the first 64 bytes
            self.logMessage("File loaded succesfully.")
            self.unpackHeader(header, filePath)
            self.executeFileButton.setEnabled(True)

    # Méthode pour éditer les éléments
    def editItem(self, item, column):
        if column == 1:  # On autorise l'édition que pour la colonne des valeurs
            self.jsonView.editItem(item, column)

    def saveModifications(self):
        footerData = self.collectFooterData()  # Utilisez cette méthode pour récupérer uniquement les données du footer
        if footerData is not None:
            self.jsonData = footerData
            self.logMessage("Modifications saved localy.")

    def collectFooterData(self):
        root = self.jsonView.invisibleRootItem()
        footerData = None
        # Parcourir tous les éléments au niveau le plus haut pour trouver le footer
        for i in range(root.childCount()):
            item = root.child(i)
            if item.text(0) == "Footer":  # Identifier l'élément "Footer"
                footerData = self.collectData(item)  # Commencer la collecte à partir de cet élément
                break  # Quitter la boucle une fois le footer trouvé
        return footerData

    def collectData(self, parentItem):
        jsonData = {}
        for i in range(parentItem.childCount()):
            item = parentItem.child(i)
            key = item.text(0)
            value = item.text(1)
            if item.childCount() > 0:
                value = self.collectData(item)  # Récurse pour les sous-éléments
            else:
                try:
                    value = json.loads(value)  # Tenter de convertir la valeur en type JSON approprié
                except json.JSONDecodeError:
                    pass  # Garder la valeur comme chaîne si la conversion échoue
            jsonData[key] = value
        return jsonData

    def unpackHeader(self, header, filePath):
        format_string1 = '4sHHIII'
        format_string2 = 'QB35x'
        data1 = struct.unpack(format_string1, header[:20])
        data2 = struct.unpack(format_string2, header[20:])
        data = data1 + data2
        magic_number, version, bits_per_pixel, img_width, img_height, img_nb, total_data_size, endianness = data

        self.data_size = total_data_size

        if magic_number.decode('utf-8') != 'HOLO':
            self.logMessage("Not a '.holo' file.")
            return

        self.loadFooterButton.setEnabled(True)

        magic_number = magic_number.decode('utf-8')
        footer = self.readFooter(filePath, total_data_size)
        self.file = filePath
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
            self.logMessage("Footer loaded.")
        else:
                # Si le footer n'existe pas ou est invalide, afficher un message et désactiver le bouton de téléchargement
                self.addItems(self.jsonView.invisibleRootItem(), {"Footer": "No footer found or it is invalid."})
                self.jsonData = None  # Réinitialiser les données JSON
                self.downloadJsonButton.setEnabled(False)  # Désactiver le bouton de téléchargement
                self.logMessage("No / incorect Footer Found")

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

    def removeExistingFooter(self):
        root = self.jsonView.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if item.text(0) == "Footer":
                # Supprimer l'élément footer existant
                root.removeChild(item)
                break


    def loadFooter(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Load Footer JSON", "", "JSON Files (*.json)", options=options)
        if fileName:
            with open(fileName, 'r') as file:
                try:
                    self.jsonData = json.load(file)
                    self.logMessage("Footer JSON loaded successfully.")

                    # Supprimez le footer existant avant d'ajouter le nouveau
                    self.removeExistingFooter()

                    # Ajoutez le nouveau footer chargé
                    self.addItems(self.jsonView.invisibleRootItem(), {"Footer": self.jsonData})

                except json.JSONDecodeError as e:
                    self.logMessage(f"Error loading JSON: {e}")

        self.overwriteFooter()

    def downloadJson(self):
            if self.jsonData is not None:
                fileName, _ = QFileDialog.getSaveFileName(self, "Save JSON File", "", "JSON Files (*.json)")
                if fileName:
                    with open(fileName, 'w') as file:
                        json.dump(self.jsonData, file, indent=4)
                    self.downloadJsonButton.setEnabled(False)

    def addItems(self, parent, json_data):
        self.jsonView.blockSignals(True)
        for key, value in json_data.items():
            if isinstance(value, (dict, list)):
                item = QTreeWidgetItem(parent, [key, ""])
                item.setFlags(item.flags() | Qt.ItemIsEditable)  # Rendre les éléments modifiables
                self.addItems(item, value) if isinstance(value, dict) else [self.addItems(item, {str(i): v}) for i, v in enumerate(value)]
            else:
                item = QTreeWidgetItem(parent, [key, str(value)])
                item.setFlags(item.flags() | Qt.ItemIsEditable)  # Rendre les éléments modifiables
        self.jsonView.blockSignals(False)

    def overwriteFooter(self):
        total_data_size = self.data_size
        self.saveModifications()

        # Ouvrez le fichier en mode 'r+b' pour lire/écrire sans effacer le contenu
        with open(self.file, 'r+b') as file:
            file.seek(total_data_size + 64)  # Positionnez-vous juste avant le début du footer présumé
            self.jsonData = self.correct_bool_values(self.jsonData)
            footerJson = json.dumps(self.jsonData)
            file.write(footerJson.encode('utf-8'))  # Écrivez le nouveau footer
            file.truncate()  # Supprimez tout ce qui se trouve après le nouveau footer
        self.overwriteFooterButton.setEnabled(False)
        self.logMessage("Changes loaded in the file.")

    def logMessage(self, message):
        self.logWindow.appendPlainText(message)  # Ajoute le message au widget de log
        # Auto-scroll
        self.logWindow.verticalScrollBar().setValue(self.logWindow.verticalScrollBar().maximum())

    def correct_bool_values(self,data):
        if isinstance(data, dict):
            return {k: self.correct_bool_values(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.correct_bool_values(v) for v in data]
        elif isinstance(data, str):
            if data == "True":
                return True
            elif data == "False":
                return False
        return data

    def onItemChanged(self, item, column):
        if column == 1:  # Seulement intéressé par les modifications de la colonne des valeurs
            key = item.text(0)  # La clé de l'élément modifié
            newValue = item.text(1)  # La nouvelle valeur
            if self.collectFooterData() == self.jsonData:
                self.overwriteFooterButton.setEnabled(False)
            else:
                self.overwriteFooterButton.setEnabled(True)

            self.logMessage(f"Item '{key}' changed to '{newValue}'.")

    def executeFile(self):

        self.overwriteFooter()
        if not self.file:
            self.logMessage("No file loaded to execute.")
            return

        try:
            if sys.platform.startswith('linux'):
                subprocess.run(['xdg-open', self.file], check=True)
            elif sys.platform.startswith('darwin'):
                subprocess.run(['open', self.file], check=True)
            elif sys.platform.startswith('win32'):
                subprocess.run(['cmd', '/c', 'start', '', self.file], check=True)
            self.logMessage(f"Executing file: {self.file}")
        except subprocess.CalledProcessError as e:
            self.logMessage(f"Failed to execute file: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = HoloFileReader()
    ex.show()
    sys.exit(app.exec())
