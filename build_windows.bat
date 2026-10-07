pip install python-barcode pillow qrcode[pil] pyinstaller
pyinstaller --onefile --name BarcodeMaker barcode_maker.py
pyinstaller --onefile --name QRMaker qr_maker.py
echo Done - see dist\BarcodeMaker.exe and dist\QRMaker.exe
