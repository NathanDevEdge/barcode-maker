#!/bin/sh
# Run after: pyinstaller --noconfirm --windowed --name LabelMakerGUI label_maker_gui.py
set -e
mkdir -p installer_out
pkgbuild --component dist/LabelMakerGUI.app --install-location /Applications \
  --identifier com.devedge.yellowlabelmaker --version 1.0 installer_out/YellowLabelMaker.pkg
