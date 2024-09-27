import subprocess
import pexpect
import sys
from PyQt5.QtWidgets import QMessageBox, QListWidgetItem, QInputDialog
from PyQt5.QtCore import Qt

def refresh_devices(self):
    self.devices_list.clear()
    try:
        result = subprocess.run(["lsblk", "-ndo", "NAME,SIZE,TYPE,MOUNTPOINT"], capture_output=True, text=True, check=True)
        devices = result.stdout.strip().split('\n')
        for device in devices:
            parts = device.split()
            if len(parts) < 3:
                continue
            name, size, dev_type = parts[:3]
            mountpoint = parts[3] if len(parts) > 3 else ""
            if dev_type == "disk" and (name.startswith('sd') or name.startswith('nvme')):
                status = "Mounted" if mountpoint else "Available"
                item = QListWidgetItem(f"/dev/{name} ({size}) - {status}")
                item.setData(Qt.UserRole, (f"/dev/{name}", mountpoint))
                self.devices_list.addItem(item)
    except subprocess.CalledProcessError as e:
        self.output_console.append(f"Error refreshing devices: {e}")

def create_raid(self):
    try:
        child = pexpect.spawn(self.command)
        child.logfile = sys.stdout.buffer

        index = child.expect(['Continue creating array?', pexpect.EOF, pexpect.TIMEOUT], timeout=30)
        if index == 0:
            self.confirmation_needed.emit()
            while not self.should_continue:
                self.msleep(100)  # Wait for user confirmation
            if self.should_continue:
                child.sendline('y')
            else:
                child.sendline('n')
                self.finished.emit(False, "RAID creation aborted by user.")
                return

        while True:
            try:
                line = child.readline().decode().strip()
                if not line:
                    break
                self.progress.emit(line)
            except pexpect.EOF:
                break

        child.close()
        if child.exitstatus == 0:
            self.finished.emit(True, "RAID creation completed successfully.")
        else:
            self.finished.emit(False, "RAID creation may have failed. Please check the output.")
    except Exception as e:
        self.finished.emit(False, f"Error: {str(e)}")

def refresh_raid_list(self):
    self.raid_list.clear()
    try:
        result = subprocess.run(["cat", "/proc/mdstat"], capture_output=True, text=True, check=True)
        raids = result.stdout.strip().split('\n')
        for line in raids:
            if line.startswith('md'):
                raid_name = line.split()[0]
                self.raid_list.addItem(raid_name)
    except subprocess.CalledProcessError as e:
        self.output_console.append(f"Error refreshing RAID list: {e}")

def delete_raid(self):
    selected_raid = self.raid_list.currentItem()
    if not selected_raid:
        QMessageBox.warning(self, "Warning", "Please select a RAID array to delete.")
        return

    raid_name = selected_raid.text()
    reply = QMessageBox.question(self, "Confirm Deletion", 
                                 f"Are you sure you want to delete {raid_name}?",
                                 QMessageBox.Yes | QMessageBox.No)
    if reply == QMessageBox.Yes:
        try:
            # Stop the RAID array
            subprocess.run(["sudo", "mdadm", "--stop", f"/dev/{raid_name}"], check=True)
            self.output_console.append(f"Stopped RAID array {raid_name}")

            # Get the component devices
            result = subprocess.run(["sudo", "mdadm", "--detail", f"/dev/{raid_name}"], 
                                    capture_output=True, text=True)
            devices = [line.split()[-1] for line in result.stdout.split('\n') if "active sync" in line]

            # Remove the RAID device
            subprocess.run(["sudo", "mdadm", "--remove", f"/dev/{raid_name}"], check=True)
            self.output_console.append(f"Removed RAID device {raid_name}")

            # Clear superblocks from all component devices
            for device in devices:
                subprocess.run(["sudo", "mdadm", "--zero-superblock", device], check=True)
                self.output_console.append(f"Cleared superblock on {device}")

            self.output_console.append(f"Successfully deleted {raid_name} and cleared all component devices")
            refresh_raid_list(self)
        except subprocess.CalledProcessError as e:
            self.output_console.append(f"Error deleting RAID: {e}")
            QMessageBox.critical(self, "Error", f"Failed to delete RAID: {e}")

def mount_raid(self):
    selected_raid = self.raid_list.currentItem()
    if not selected_raid:
        QMessageBox.warning(self, "Warning", "Please select a RAID array to mount.")
        return

    raid_name = selected_raid.text()
    mount_point, ok = QInputDialog.getText(self, "Mount Point", "Enter mount point:")
    if ok and mount_point:
        try:
            subprocess.run(["pkexec", "mkdir", "-p", mount_point], check=True)
            subprocess.run(["pkexec", "mount", f"/dev/{raid_name}", mount_point], check=True)
            self.output_console.append(f"Successfully mounted {raid_name} to {mount_point}")
        except subprocess.CalledProcessError as e:
            self.output_console.append(f"Error mounting RAID: {e}")
            QMessageBox.critical(self, "Error", f"Failed to mount RAID: {e}")

def unmount_raid(self):
    selected_raid = self.raid_list.currentItem()
    if not selected_raid:
        QMessageBox.warning(self, "Warning", "Please select a RAID array to unmount.")
        return

    raid_name = selected_raid.text()
    try:
        result = subprocess.run(["findmnt", "-n", "-o", "TARGET", f"/dev/{raid_name}"], 
                                capture_output=True, text=True, check=True)
        mount_point = result.stdout.strip()
        if mount_point:
            subprocess.run(["sudo", "umount", mount_point], check=True)
            self.output_console.append(f"Successfully unmounted {raid_name} from {mount_point}")
        else:
            self.output_console.append(f"{raid_name} is not currently mounted.")
    except subprocess.CalledProcessError as e:
        self.output_console.append(f"Error unmounting RAID: {e}")
        QMessageBox.critical(self, "Error", f"Failed to unmount RAID: {e}")

def create_filesystem(self):
    selected_raid = self.raid_list.currentItem()
    if not selected_raid:
        QMessageBox.warning(self, "Warning", "Please select a RAID array.")
        return

    raid_name = selected_raid.text()
    filesystem_type, ok = QInputDialog.getItem(self, "Filesystem Type", 
                                               "Select filesystem type:",
                                               ["ext4", "xfs", "btrfs"], 0, False)
    if ok and filesystem_type:
        try:
            command = f"pkexec mkfs.{filesystem_type} /dev/{raid_name}"
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate()
            if process.returncode == 0:
                self.output_console.append(f"Successfully created {filesystem_type} filesystem on {raid_name}")
            else:
                raise subprocess.CalledProcessError(process.returncode, command, output, error)
        except subprocess.CalledProcessError as e:
            self.output_console.append(f"Error creating filesystem: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create filesystem: {e}")

def add_drive_to_raid(self):
    selected_raid = self.raid_list.currentItem()
    if not selected_raid:
        QMessageBox.warning(self, "Warning", "Please select a RAID array to add a drive to.")
        return

    raid_name = selected_raid.text()
    new_drive, ok = QInputDialog.getText(self, "Add Drive", "Enter the path of the new drive (e.g., /dev/sdd):")
    if ok and new_drive:
        try:
            subprocess.run(["sudo", "mdadm", "--add", f"/dev/{raid_name}", new_drive], check=True)
            self.output_console.append(f"Successfully added {new_drive} to {raid_name}")
        except subprocess.CalledProcessError as e:
            self.output_console.append(f"Error adding drive to RAID: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add drive to RAID: {e}")
