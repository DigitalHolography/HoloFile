from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QTreeWidget, QTreeWidgetItem, QHeaderView, QPlainTextEdit, QTabWidget, QHBoxLayout, QLabel, QLineEdit
from PySide6.QtCore import Qt
import sys
import subprocess
import struct
import json
import os

class HoloFileReader(QWidget):
    def __init__(self):
        super().__init__()
        self.jsonData = None
        self.file = ""
        self.data_size = 0
        self.appVersion = "1.5"
        self.headerValues = {'Magic Number': 'HOLO', 'Version': 0, 'Bits per Pixel': 0, 'Image Width': 0, 'Image Height': 0, 'Image Number': 0, 'Total Data Size': 0, 'Endianness': 0}
        self.initUI()


    def initUI(self):
        self.setWindowTitle('Holo file inspector (' + self.appVersion + ' ver)')
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout()

        self.tabWidget = QTabWidget()
        layout.addWidget(self.tabWidget)

        self.fileTab = QWidget()
        self.advancedTab = QWidget()

        self.tabWidget.addTab(self.fileTab, "File")
        self.tabWidget.addTab(self.advancedTab, "Advanced")

        self.initFileTab()
        self.initAdvancedTab()

        self.logWindow = QPlainTextEdit()
        self.logWindow.setReadOnly(True)
        self.logWindow.setMaximumHeight(100)
        layout.addWidget(self.logWindow)

        self.setLayout(layout)


    def initFileTab(self):
        layout = QVBoxLayout(self.fileTab)

        self.openButton = QPushButton('Open Holo File')
        self.openButton.clicked.connect(self.openFileDialog)
        layout.addWidget(self.openButton)

        self.overwriteFooterButton = QPushButton('Overwrite Footer')
        self.overwriteFooterButton.clicked.connect(self.overwriteFooter)
        self.overwriteFooterButton.setEnabled(False)
        layout.addWidget(self.overwriteFooterButton)

        self.loadFooterButton = QPushButton('Load Footer (JSON)')
        self.loadFooterButton.clicked.connect(self.loadFooter)
        self.loadFooterButton.setEnabled(False)
        layout.addWidget(self.loadFooterButton)

        self.downloadJsonButton = QPushButton('Save Footer (JSON)')
        self.downloadJsonButton.clicked.connect(self.downloadJson)
        self.downloadJsonButton.setEnabled(False)
        layout.addWidget(self.downloadJsonButton)

        self.removeJsonButton = QPushButton('Remove Footer')
        self.removeJsonButton.clicked.connect(self.removeJson)
        self.removeJsonButton.setEnabled(False)
        layout.addWidget(self.removeJsonButton)

        self.jsonView = QTreeWidget()
        self.jsonView.setHeaderLabels(["Key", "Value"])
        self.jsonView.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.jsonView.itemDoubleClicked.connect(self.editItem)
        self.jsonView.itemChanged.connect(self.onItemChanged)
        layout.addWidget(self.jsonView)

        self.executeFileButton = QPushButton('Execute File')
        self.executeFileButton.clicked.connect(self.executeFile)
        self.executeFileButton.setEnabled(False)
        layout.addWidget(self.executeFileButton)


    def initAdvancedTab(self):
        layout = QVBoxLayout(self.advancedTab)
        self.headerEdits = {}
        for key in self.headerValues.keys():
            row = QHBoxLayout()
            label = QLabel(key + ':')
            edit = QLineEdit(str(self.headerValues[key]))
            edit.textChanged.connect(lambda value, key=key: self.onHeaderEditChanged(key, value))
            self.headerEdits[key] = edit
            row.addWidget(label)
            row.addWidget(edit)
            layout.addLayout(row)

        saveButton = QPushButton('Save Header Changes')
        saveButton.clicked.connect(self.saveHeaderChanges)
        layout.addWidget(saveButton)

    def onHeaderEditChanged(self, key, value):
            self.headerValues[key] = value

    def saveHeaderChanges(self):
        try:
            magic_number = self.headerValues['Magic Number'].encode('utf-8')
            version = int(self.headerValues['Version'])
            bits_per_pixel = int(self.headerValues['Bits per Pixel'])
            img_width = int(self.headerValues['Image Width'])
            img_height = int(self.headerValues['Image Height'])
            img_nb = int(self.headerValues['Image Number'])
            total_data_size = int(self.headerValues['Total Data Size'])
            endianness = int(self.headerValues['Endianness'])

            format_string1 = '4sHHIII'
            format_string2 = 'QB35x'

            header_part1 = struct.pack(format_string1, magic_number, version, bits_per_pixel, img_width, img_height, img_nb)
            header_part2 = struct.pack(format_string2, total_data_size, endianness)

            full_header = header_part1 + header_part2

            if len(full_header) != 64:
                self.logMessage(f"Error: Header size is {len(full_header)} bytes; expected 64 bytes.")
                return

            with open(self.file, 'r+b') as file:
                file.write(full_header)
                self.logMessage("Header saved successfully.")
        except Exception as e:
            self.logMessage(f"Error saving header: {e}")

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

    def editItem(self, item, column):
        if column == 1:
            self.jsonView.editItem(item, column)

    def saveModifications(self):
        footerData = self.collectFooterData()
        if footerData is not None:
            self.jsonData = footerData

    def collectFooterData(self):
        root = self.jsonView.invisibleRootItem()
        footerData = None

        for i in range(root.childCount()):
            item = root.child(i)
            if item.text(0) == "Footer":
                footerData = self.collectData(item)
                break
        return footerData

    def collectData(self, parentItem):
        jsonData = {}
        for i in range(parentItem.childCount()):
            item = parentItem.child(i)
            key = item.text(0)
            value = item.text(1)
            if item.childCount() > 0:
                value = self.collectData(item)
            else:
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    pass
            jsonData[key] = value
        return jsonData

    def updateAdvancedTabUI(self):
        for key, value in self.headerValues.items():
            if key in self.headerEdits:
                self.headerEdits[key].setText(str(value))

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

        self.headerValues['Magic Number'] = magic_number
        self.headerValues['Version'] = version
        self.headerValues['Bits per Pixel'] = bits_per_pixel
        self.headerValues['Image Width'] = img_width
        self.headerValues['Image Height'] = img_height
        self.headerValues['Image Number'] = img_nb
        self.headerValues['Total Data Size'] = total_data_size
        self.headerValues['Endianness'] = endianness

        self.updateAdvancedTabUI()

        if isinstance(footer, dict):
            self.addItems(self.jsonView.invisibleRootItem(), {"Footer": footer})
            self.logMessage("Footer loaded.")
        else:
                self.addItems(self.jsonView.invisibleRootItem(), {"Footer": "No footer found or it is invalid."})
                self.jsonData = None
                self.downloadJsonButton.setEnabled(False)
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
                    self.removeJsonButton.setEnabled(True)
                    return footer
                except json.JSONDecodeError:
                    return 'Invalid JSON footer.'
        return 'No footer found.'

    def removeExistingFooter(self):
        root = self.jsonView.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if item.text(0) == "Footer":
                root.removeChild(item)
                break

    def removeJson(self):
        if not self.file or self.data_size == 0:
            self.logMessage("No file or data size information available.")
            return

        # Open the file in read+write binary mode ('r+b')
        with open(self.file, 'r+b') as file:
            # Seek to the start of the JSON footer, which is right after the main data
            # This position is determined by the total data size + the header length (64 bytes)
            file.seek(self.data_size + 64)

            # Truncate the file at this point to remove the footer
            file.truncate()

        # Update UI and internal state to reflect the removal of the JSON footer
        self.jsonData = None  # Clear any loaded JSON data
        self.removeExistingFooter()  # Remove the footer from the UI if it was displayed
        self.downloadJsonButton.setEnabled(False)  # Disable the download button as there is no JSON to save
        self.removeJsonButton.setEnabled(False)  # Disable the remove button as there is no JSON to remove
        self.logMessage("Footer removed successfully.")


    def loadFooter(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Load Footer JSON", "", "JSON Files (*.json)", options=options)
        if fileName:
            with open(fileName, 'r') as file:
                try:
                    self.jsonData = json.load(file)
                    self.logMessage("Footer JSON loaded successfully.")

                    self.removeExistingFooter()

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

        with open(self.file, 'r+b') as file:
            file.seek(total_data_size + 64)
            self.jsonData = self.correct_bool_values(self.jsonData)
            footerJson = json.dumps(self.jsonData)
            file.write(footerJson.encode('utf-8'))
            file.truncate()
        self.overwriteFooterButton.setEnabled(False)
        self.logMessage("Changes loaded in the file.")

    def logMessage(self, message):
        self.logWindow.appendPlainText(message)
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
        if column == 1:
            key = item.text(0)
            newValue = item.text(1)
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
