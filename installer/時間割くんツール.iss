#define MyAppName "時間割くん管理ツール"
#define MyAppVersion "3.0"
#define MyAppPublisher "REK_PythonDev"
#define MyAppExeName "時間割くんドライバ-v3.0.exe"

[Setup]
AppId={{D28EEC4F-F047-4A76-8EAE-86C74F9CE9E7}
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
OutputBaseFilename=時間割くん管理ツールインストーラー
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\時間割くんツール\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\時間割くんツール\ConfigEditor.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\時間割くんツール\時間割くんチェッカー-v1.4.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\時間割くんツール\TimetableChecker.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\時間割くんツール\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\時間割くんドライバ"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{autodesktop}\時間割くんチェッカー"; Filename: "{app}\時間割くんチェッカー-v1.4.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
