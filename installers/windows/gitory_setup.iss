; Gitory Inno Setup Script
; Generates a modern Windows Setup Installation Wizard for Gitory

#define MyAppName "Gitory"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Gitory Open Source Team"
#define MyAppURL "https://github.com/ZVAXEROWS/Gitory"
#define MyAppExeName "Gitory.exe"
#define MyAppSourceDir "..\..\dist\Gitory"

[Setup]
; Unique App ID for Gitory
AppId={{D37E601B-A045-42E1-A4D0-A2272828C59A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
; Install in Program Files or local Programs folder without forcing elevation prompt
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Output location for the setup installation wizard executable
OutputDir=..\..\dist\installers
OutputBaseFilename=Gitory-Setup-{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; We ignore PORTABLE_MODE so wizard installations behave as installed native desktop software
Source: "{#MyAppSourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "PORTABLE_MODE,PORTABLE_README.txt,gitory_data"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
