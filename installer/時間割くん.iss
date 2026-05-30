#define MyAppName "時間割くん"
#define MyAppVersion "1.0.5"
#define MyAppPublisher "REK_PythonDev"
#define MyAppExeName "時間割くん-v1.0.5.exe"

[Setup]
AppId={{166DE9B4-1852-4E0F-A8DD-0A3998B3D814}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} のアンインストール
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
OutputDir=..\release
OutputBaseFilename=時間割くんインストーラー
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\時間割くん\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\時間割くん\TimeManager.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\時間割くん\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
