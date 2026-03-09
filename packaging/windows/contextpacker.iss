#define MyAppName "ContextPacker"
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef RepoRoot
  #error "RepoRoot must be provided to the Inno Setup compiler."
#endif
#ifndef DistDir
  #define DistDir RepoRoot + "\dist\ContextPacker"
#endif

[Setup]
AppId={{2C46E0B5-5F04-4C18-8E9A-1D93A1C1D9F7}
AppName={#MyAppName}
AppVersion={#AppVersion}
AppPublisher=ContextPacker
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile={#RepoRoot}\LICENSE
OutputDir={#RepoRoot}\release
OutputBaseFilename=ContextPacker-{#AppVersion}-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\ContextPacker.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#RepoRoot}\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\ContextPacker.exe"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\ContextPacker.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\ContextPacker.exe"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
