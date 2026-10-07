# Changelog

## v1.0.1
### Fixed
- Barcodes failed to generate in the installed app on Windows and macOS ("0 images created"). The font used to print the digits under the bars was missing from the packaged app and is now included.

## v1.0.0
### Added
- Yellow barcode generator: reads `UPC Code / Barcode`, names files from `Supplier Description`.
- Yellow QR code generator: encodes `Supplier Code`, names files from `Supplier Description`.
- Simple GUI main menu with **Generate Barcodes** and **Generate QR Codes** buttons, plus a message showing where the output was saved.
- Windows installer (`YellowLabelMaker-Setup.exe`) and macOS installer (`YellowLabelMaker.pkg`) with everything bundled.
