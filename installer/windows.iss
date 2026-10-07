[Setup]
AppName=Yellow Label Maker
AppVersion=1.0
DefaultDirName={autopf}\Yellow Label Maker
DefaultGroupName=Yellow Label Maker
OutputDir=..\installer_out
OutputBaseFilename=YellowLabelMaker-Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\LabelMakerGUI.exe

[Files]
Source: "..\dist\LabelMakerGUI\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\Yellow Label Maker"; Filename: "{app}\LabelMakerGUI.exe"
Name: "{autodesktop}\Yellow Label Maker"; Filename: "{app}\LabelMakerGUI.exe"

[Run]
Filename: "{app}\LabelMakerGUI.exe"; Description: "Launch Yellow Label Maker"; Flags: nowait postinstall skipifsilent
