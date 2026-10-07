# Barcode Maker + QR Maker

Converts a product CSV into yellow barcode images (black bars on yellow, PNG).

- Barcode number comes from the `UPC Code / Barcode` column
- File name comes from the `Supplier Description` column
- Output goes to a `Yellow Barcodes` folder next to the CSV

## QR Maker
Same idea, but encodes the `Supplier Code` column as a QR code (black on yellow). Output goes to `Yellow QR Codes`.
Run `QRMaker` (or `python qr_maker.py`).

## GUI
`LabelMakerGUI` (or `python label_maker_gui.py`): pick a CSV, tick Barcodes and/or QR codes, click Generate.

## Use
Run `BarcodeMaker` (or `python barcode_maker.py`), paste the CSV path when asked.

## Build
Executables for Windows and macOS are built by the GitHub Actions workflow (Actions tab -> Build -> artifacts),
or locally with `pip install python-barcode pillow pyinstaller` then `pyinstaller --onefile --name BarcodeMaker barcode_maker.py`.
