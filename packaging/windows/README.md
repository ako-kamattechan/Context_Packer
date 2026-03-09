# Windows release

Prerequisites:

- Python 3.10+
- Inno Setup 6 (optional if you only want the unpacked `dist/ContextPacker` bundle)

Build commands:

```powershell
.\scripts\build_windows.ps1
```

Skip the installer and only build the executable bundle:

```powershell
.\scripts\build_windows.ps1 -SkipInstaller
```

Outputs:

- `dist/ContextPacker/ContextPacker.exe`
- `release/ContextPacker-<version>-Setup.exe` when Inno Setup is available
