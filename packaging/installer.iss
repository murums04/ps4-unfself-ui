#ifndef AppVersion
  #define AppVersion "0.1.1"
#endif
#ifndef PayloadDir
  #error PayloadDir must point to the built application directory
#endif
#ifndef OutputDir
  #error OutputDir must be explicit
#endif
[Setup]
AppId={{9C1623D7-1B18-4F87-A62C-F6A88C16B4B5}
AppName=murums PS4 Unfself UI
AppVersion={#AppVersion}
AppPublisher=murums
DefaultDirName={localappdata}\Programs\murums\PS4 Unfself UI
DefaultGroupName=murums PS4 Unfself UI
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
OutputDir={#OutputDir}
OutputBaseFilename=ps4-unfself-ui-{#AppVersion}-windows-x64-setup
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\PS4 Unfself UI.exe
LicenseFile=..\LICENSE
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
SetupLogging=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "Desktop shortcut"; Flags: unchecked

[Files]
Source: "{#PayloadDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\PS4 Unfself UI"; Filename: "{app}\PS4 Unfself UI.exe"
Name: "{autodesktop}\PS4 Unfself UI"; Filename: "{app}\PS4 Unfself UI.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\PS4 Unfself UI.exe"; Description: "Open PS4 Unfself UI"; Flags: nowait postinstall skipifsilent

