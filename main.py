import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QComboBox, QListWidget, QPushButton, QTabWidget, 
                             QTextEdit, QMessageBox, QListWidgetItem, QInputDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from raid_functions import (refresh_devices, create_raid, refresh_raid_list, delete_raid, 
                            mount_raid, unmount_raid, add_drive_to_raid, create_filesystem)

class RAIDCreationWorker(QThread):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)
    confirmation_needed = pyqtSignal()

    def __init__(self, command):
        super().__init__()
        self.command = command
        self.should_continue = False

    def run(self):
        create_raid(self)

class RAIDManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RAID Manager")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        self.setup_create_raid_tab()
        self.setup_manage_raid_tab()
        self.setup_learn_more_tab()

    def setup_create_raid_tab(self):
        create_raid_tab = QWidget()
        layout = QVBoxLayout(create_raid_tab)

        # RAID level selection
        raid_level_layout = QHBoxLayout()
        raid_level_layout.addWidget(QLabel("RAID Level:"))
        self.raid_level_combo = QComboBox()
        self.raid_level_combo.addItems(["RAID 0", "RAID 1", "RAID 5", "RAID 6", "RAID 10"])
        raid_level_layout.addWidget(self.raid_level_combo)
        layout.addLayout(raid_level_layout)

        # Available devices
        layout.addWidget(QLabel("Available Devices:"))
        self.devices_list = QListWidget()
        self.devices_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.devices_list)

        # Refresh devices button
        refresh_button = QPushButton("Refresh Devices")
        refresh_button.clicked.connect(self.refresh_devices)
        layout.addWidget(refresh_button)

        # Create RAID button
        create_button = QPushButton("Create RAID")
        create_button.clicked.connect(self.create_raid)
        layout.addWidget(create_button)

        # Output console
        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        layout.addWidget(QLabel("Output:"))
        layout.addWidget(self.output_console)

        self.tab_widget.addTab(create_raid_tab, "Create RAID")

    def setup_manage_raid_tab(self):
        manage_raid_tab = QWidget()
        layout = QVBoxLayout(manage_raid_tab)

        # List of existing RAID arrays
        layout.addWidget(QLabel("Existing RAID Arrays:"))
        self.raid_list = QListWidget()
        layout.addWidget(self.raid_list)

        # Refresh RAID list button
        refresh_raid_button = QPushButton("Refresh RAID List")
        refresh_raid_button.clicked.connect(self.refresh_raid_list)
        layout.addWidget(refresh_raid_button)

        # RAID management buttons
        button_layout = QHBoxLayout()
        delete_button = QPushButton("Delete RAID")
        delete_button.clicked.connect(self.delete_raid)
        button_layout.addWidget(delete_button)

        create_fs_button = QPushButton("Create Filesystem")
        create_fs_button.clicked.connect(self.create_filesystem)
        button_layout.addWidget(create_fs_button)

        mount_button = QPushButton("Mount RAID")
        mount_button.clicked.connect(self.mount_raid)
        button_layout.addWidget(mount_button)

        unmount_button = QPushButton("Unmount RAID")
        unmount_button.clicked.connect(self.unmount_raid)
        button_layout.addWidget(unmount_button)

        add_drive_button = QPushButton("Add Drive to RAID")
        add_drive_button.clicked.connect(self.add_drive_to_raid)
        button_layout.addWidget(add_drive_button)

        layout.addLayout(button_layout)

        self.tab_widget.addTab(manage_raid_tab, "Manage RAID")

    def setup_learn_more_tab(self):
        learn_more_tab = QWidget()
        layout = QVBoxLayout(learn_more_tab)

        learn_more_text = QTextEdit()
        learn_more_text.setReadOnly(True)
        learn_more_text.setHtml("""
        <h2>RAID Management Guide</h2>
        <p>This application allows you to create and manage RAID arrays using mdadm on Ubuntu 22.04.</p>
        <h3>Features:</h3>
        <ul>
            <li>Create RAID arrays of various levels (0, 1, 5, 6, 10)</li>
            <li>View and manage existing RAID arrays</li>
            <li>Mount and unmount RAID arrays</li>
            <li>Add drives to existing RAID arrays</li>
        </ul>
        <h3>RAID Levels:</h3>
        <ul>
            <li><strong>RAID 0:</strong> Striping for improved performance, no redundancy.</li>
            <li><strong>RAID 1:</strong> Mirroring for redundancy, requires at least 2 devices.</li>
            <li><strong>RAID 5:</strong> Striping with distributed parity, requires at least 3 devices.</li>
            <li><strong>RAID 6:</strong> Striping with double distributed parity, requires at least 4 devices.</li>
            <li><strong>RAID 10:</strong> Combination of mirroring and striping, requires at least 4 devices.</li>
        </ul>
        """)
        layout.addWidget(learn_more_text)

        self.tab_widget.addTab(learn_more_tab, "Learn More")

    def refresh_devices(self):
        refresh_devices(self)

    def create_raid(self):
        raid_level = self.raid_level_combo.currentText().split()[1]
        selected_items = self.devices_list.selectedItems()
        selected_devices = [item.data(Qt.UserRole)[0] for item in selected_items]

        if not selected_devices:
            QMessageBox.warning(self, "Warning", "Please select at least one device.")
            return

        min_devices = {"0": 2, "1": 2, "5": 3, "6": 4, "10": 4}
        if len(selected_devices) < min_devices[raid_level]:
            QMessageBox.warning(self, "Warning", f"RAID {raid_level} requires at least {min_devices[raid_level]} devices.")
            return

        command = f"sudo mdadm --create --verbose /dev/md0 --level={raid_level} --raid-devices={len(selected_devices)} {' '.join(selected_devices)}"

        self.output_console.append(f"Creating RAID {raid_level} with devices: {', '.join(selected_devices)}")
        self.output_console.append(f"Running command: {command}")

        self.worker = RAIDCreationWorker(command)
        self.worker.progress.connect(self.update_output)
        self.worker.finished.connect(self.raid_creation_finished)
        self.worker.confirmation_needed.connect(self.show_confirmation_dialog)
        self.worker.start()

    def update_output(self, line):
        self.output_console.append(line)

    def raid_creation_finished(self, success, message):
        self.output_console.append(message)
        if success:
            QMessageBox.information(self, "Success", "RAID array created successfully!")
            self.refresh_raid_list()
        else:
            QMessageBox.warning(self, "Warning", message)

    def show_confirmation_dialog(self):
        reply = QMessageBox.question(self, "Confirm RAID Creation", 
                                     "Do you want to continue creating the RAID array?",
                                     QMessageBox.Yes | QMessageBox.No)
        self.worker.should_continue = (reply == QMessageBox.Yes)

    def refresh_raid_list(self):
        refresh_raid_list(self)

    def delete_raid(self):
        delete_raid(self)

    def mount_raid(self):
        mount_raid(self)

    def unmount_raid(self):
        unmount_raid(self)

    def add_drive_to_raid(self):
        add_drive_to_raid(self)

    def create_filesystem(self):
        create_filesystem(self)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RAIDManagerApp()
    window.show()
    sys.exit(app.exec_())
