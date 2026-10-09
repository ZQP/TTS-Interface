; =====================================================================
; Inno Setup Script for Gemini TTS Studio
; Configured for Per-User Non-Admin Windows Installation
; (Installs into %LOCALAPPDATA%\Programs\GeminiTTSStudio without UAC elevation)
; =====================================================================

#define MyAppName "Gemini TTS Studio"
#define MyAppVersion "3.1.1"
#define MyAppPublisher "ZQP"
#define MyAppURL "https://github.com/ZQP/TTS-Interface"
#define MyAppExeName "GeminiTTSStudio.exe"

[Setup]
; Unique GUID for Gemini TTS Studio
AppId={{D37F8E80-6072-4B6A-9BA3-570E48228CF7}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases

; Per-User Installation: No Admin Privileges or UAC prompt required!
DefaultDirName={localappdata}\Programs\GeminiTTSStudio
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

DisableProgramGroupPage=yes
OutputDir=dist\installer
OutputBaseFilename=GeminiTTSStudio-Setup-{#MyAppVersion}
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\assets\icon.ico

; Modern Compression & Wizard
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

; Ensure running instance is closed before update/uninstall
CloseApplications=yes
CloseApplicationsFilter=*.exe

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Standalone Executable and Assets
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\icon.ico"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "assets\icon.png"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "assets\header_logo.png"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: ".env.example"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Windows Start Menu and Desktop Shortcuts
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"; Tasks: desktopicon

[Run]
; Option to launch after installation finishes
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up temp files created in app folder if any
Type: filesandordirs; Name: "{app}\assets"
