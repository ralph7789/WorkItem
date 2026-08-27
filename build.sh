#!/bin/bash
set -e

TARGET=$1

if [ "$TARGET" == "--win" ]; then
    echo "=== Building WorkItems App for WINDOWS ==="
    # Check if wine is installed
    if ! command -v wine &> /dev/null; then
        echo "Error: 'wine' is required for Windows cross-compilation on Linux."
        exit 1
    fi

    # Set up wine prefix specifically for python
    export WINEPREFIX="$(pwd)/.wine_env"
    
    # Check if python is installed in wine
    if ! wine python --version &> /dev/null; then
        echo "Windows Python not found in Wine. Downloading and installing Python 3.11 for Windows..."
        wget -q https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe -O python-installer.exe
        echo "Installing Python (this may take a minute)..."
        wine python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
        rm python-installer.exe
    fi

    echo "Installing requirements in Wine Python..."
    wine python -m pip install --upgrade pip
    wine python -m pip install PySide6 peewee PyGithub keyring pyinstaller

    echo "Building Windows Executable..."
    wine python -m PyInstaller --onefile --windowed --name WorkItems_Windows \
        --exclude-module PySide6.QtWebEngineCore \
        --exclude-module PySide6.QtWebEngineWidgets \
        --exclude-module PySide6.QtQml \
        --exclude-module PySide6.QtQuick \
        --exclude-module PySide6.QtSql \
        --exclude-module PySide6.QtNetwork \
        --exclude-module PySide6.QtSensors \
        --exclude-module PySide6.QtWebChannel \
        --exclude-module PySide6.QtPositioning \
        --exclude-module PySide6.QtMultimedia \
        --exclude-module PySide6.QtBluetooth \
        --exclude-module PySide6.QtSerialPort \
        --exclude-module PySide6.Qt3DCore \
        --exclude-module PySide6.Qt3DRender \
        --exclude-module PySide6.Qt3DInput \
        --exclude-module PySide6.Qt3DLogic \
        --add-data "style_analogue.qss;." \
        --add-data "style_classic.qss;." \
        --hidden-import keyring.backends.Windows \
        --hidden-import src.e2e_test \
        src/ui/main_window.py

    echo "Build complete! Windows Executable is located in the 'dist/' folder."

elif [ "$TARGET" == "--linux" ] || [ -z "$TARGET" ]; then
    echo "=== Building WorkItems App for LINUX ==="
    ./venv/bin/pyinstaller --onefile --windowed --name WorkItems \
        --exclude-module PySide6.QtWebEngineCore \
        --exclude-module PySide6.QtWebEngineWidgets \
        --exclude-module PySide6.QtQml \
        --exclude-module PySide6.QtQuick \
        --exclude-module PySide6.QtSql \
        --exclude-module PySide6.QtNetwork \
        --exclude-module PySide6.QtSensors \
        --exclude-module PySide6.QtWebChannel \
        --exclude-module PySide6.QtPositioning \
        --exclude-module PySide6.QtMultimedia \
        --exclude-module PySide6.QtBluetooth \
        --exclude-module PySide6.QtSerialPort \
        --exclude-module PySide6.Qt3DCore \
        --exclude-module PySide6.Qt3DRender \
        --exclude-module PySide6.Qt3DInput \
        --exclude-module PySide6.Qt3DLogic \
        --add-data "style_analogue.qss:." \
        --add-data "style_classic.qss:." \
        --hidden-import keyring.backends.SecretService \
        --hidden-import keyring.backends.kwallet \
        --hidden-import keyring.backends.chainer \
        --hidden-import src.e2e_test \
        src/ui/main_window.py
        
    echo "Build complete! Linux Executable is located in the 'dist/' folder."
else
    echo "Usage: ./build.sh [--linux | --win]"
fi
