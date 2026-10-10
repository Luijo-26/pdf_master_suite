; ========================================================
; Script de Inno Setup 6 para PDF Master Suite
; Genera el instalador oficial para Windows (64-bit)
; ========================================================

#ifndef MyAppVersion
#define MyAppVersion "2.3.0"
#endif

#define MyAppName "PDF Master Suite"
#define MyAppPublisher "PDF Master"
#define MyAppURL "https://github.com/Luijo-26/pdf_master_suite"
#define MyAppExeName "PDFMasterSuite.exe"

[Setup]
; Identificador único permanente para reconocer la instalación en el registro
AppId={{8B190204-7D7A-4569-801D-3C9A6AE1B981}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases

; Instalación por usuario (en %LocalAppData%\Programs\PDFMasterSuite)
; PrivilegesRequired=lowest permite instalar y auto-actualizar sin requerir permisos de Administrador (UAC)
DefaultDirName={localappdata}\Programs\PDFMasterSuite
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest

OutputDir=dist\installer
OutputBaseFilename=PDFMasterSuite_Setup
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible

; Cierra instancias abiertas durante una actualización o desinstalación
CloseApplications=yes
RestartApplications=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Copia todos los archivos y librerías generados por PyInstaller en dist\PDFMasterSuite
Source: "dist\app_package\PDFMasterSuite\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
