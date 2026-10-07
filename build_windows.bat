pip install python-barcode pillow qrcode[pil] pyinstaller
pyinstaller --onefile --name BarcodeMaker barcode_maker.py
pyinstaller --onefile --name QRMaker qr_maker.py
pyinstaller --onefile --windowed --name LabelMakerGUI label_maker_gui.py
echo Done - see dist\BarcodeMaker.exe and dist\QRMaker.exe and dist\LabelMakerGUI.exe
