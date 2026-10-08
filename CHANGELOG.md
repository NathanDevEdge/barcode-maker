# Changelog

## v1.1.0

### Added
- A brand-new look: hazard-tape styling, light and dark themes, and a mascot (Barry) whose eyes follow your mouse.
- Live preview of the first barcode and QR code as soon as you pick a CSV.
- Progress bar, rotating silly status messages, a scanner beep and confetti when a run finishes.
- Lifetime counter of labels made (saved on your computer).
- The app remembers the last CSV you used.
- Label colour picker (yellow by default).
- Optional printable A4 PDF sheet of all labels, in addition to the PNG folder (off by default).
- A few easter eggs. Try poking Barry.

### Changed
- PNG output is unchanged: one image per row, named from `Supplier Description`, in the same output folders.

## v1.0.1
### Fixed
- Barcodes failed to generate in the installed app on Windows and macOS ("0 images created"). The font used to print the digits under the bars was missing from the packaged app and is now included.

## v1.0.0
### Added
- Yellow barcode generator: reads `UPC Code / Barcode`, names files from `Supplier Description`.
- Yellow QR code generator: encodes `Supplier Code`, names files from `Supplier Description`.
- Simple GUI main menu with **Generate Barcodes** and **Generate QR Codes** buttons, plus a message showing where the output was saved.
- Windows installer (`YellowLabelMaker-Setup.exe`) and macOS installer (`YellowLabelMaker.pkg`) with everything bundled.
