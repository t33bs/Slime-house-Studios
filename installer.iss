#define AppName "Slime House Studios"
#define AppVersion "0.6.0"
[Setup]
AppId={{D95E4F18-6E5A-4DA6-9123-2C8A99D7A101}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Slime House Studios
DefaultDirName={autopf}\Slime House Studios
DefaultGroupName=Slime House Studios
OutputDir=installer-output
OutputBaseFilename=SlimeHouseStudios-v0.6-Setup
Compression=lzma2
SolidCompression=yes
SetupIconFile=assets\slime_house_studios.ico
UninstallDisplayIcon={app}\SlimeHouseStudios.exe
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "dist\SlimeHouseStudios.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Slime House Studios"; Filename: "{app}\SlimeHouseStudios.exe"
Name: "{autodesktop}\Slime House Studios"; Filename: "{app}\SlimeHouseStudios.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Run]
Filename: "{app}\SlimeHouseStudios.exe"; Description: "Launch Slime House Studios"; Flags: nowait postinstall skipifsilent
