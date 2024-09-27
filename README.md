# RAID Manager

RAID Manager is a graphical user interface (GUI) application for creating and managing RAID arrays on Ubuntu systems. It provides an easy-to-use interface for common RAID operations using the mdadm utility.

## Features

- Create RAID arrays (levels 0, 1, 5, 6, and 10)
- Delete existing RAID arrays
- Mount and unmount RAID arrays
- Add drives to existing RAID arrays
- Create filesystems on RAID arrays
- View available devices and existing RAID arrays

## Prerequisites

- Ubuntu 22.04 or later
- Python 3.8 or later
- PyQt5
- mdadm
- policykit-1

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/raid-manager.git
   cd raid-manager
   ```

2. Install the required dependencies:
   ```
   sudo apt-get update
   sudo apt-get install python3-pyqt5 mdadm policykit-1
   pip install pexpect
   ```

## Usage

Run the application with sudo privileges:

```
sudo python3 main.py
```

### Creating a RAID Array

1. In the "Create RAID" tab, select the desired RAID level from the dropdown menu.
2. Choose the devices you want to include in the RAID array from the list of available devices.
3. Click the "Create RAID" button.
4. Follow the prompts to confirm the RAID creation.

### Managing RAID Arrays

In the "Manage RAID" tab, you can:

- View existing RAID arrays
- Delete a RAID array
- Create a filesystem on a RAID array
- Mount and unmount RAID arrays
- Add a drive to an existing RAID array

### Learning More

The "Learn More" tab provides information about different RAID levels and their use cases.

## Warning

RAID operations can lead to data loss if not performed correctly. Always ensure you have backups of important data before creating, modifying, or deleting RAID arrays.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- This application uses mdadm for RAID operations
- GUI is built using PyQt5
