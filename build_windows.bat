pip install python-barcode pillow qrcode[pil] pyinstaller
pyinstaller --noconfirm --windowed --name LabelMakerGUI label_maker_gui.py
echo Built dist\LabelMakerGUI\LabelMakerGUI.exe
echo To make the installer, open installer\windows.iss in Inno Setup (jrsoftware.org) and click Compile.
