import os
import sys
import shutil
import subprocess
from pathlib import Path


def run_pyinstaller(entry: Path, icon: Path, name: str = "FRIDAY") -> Path:
	# Clean previous artifacts
	for p in (entry.parent / "build", entry.parent / "dist"):
		if p.exists():
			shutil.rmtree(p, ignore_errors=True)
	# Remove stale spec file
	spec_file = entry.parent / f"{name}.spec"
	if spec_file.exists():
		spec_file.unlink()

	args = [
		"--noconfirm",
		"--noconsole",
		"--onefile",
		f"--icon={icon}",
		f"--name={name}",
		str(entry),
	]

	print("[FRIDAY] Building executable with PyInstaller...")

	# Prefer programmatic API; fallback to CLI if import fails
	try:
		from PyInstaller.__main__ import run as pyinstaller_run  # type: ignore
		pyinstaller_run(args)
	except Exception:
		cmd = [sys.executable, "-m", "PyInstaller"] + args
		subprocess.check_call(cmd)

	dist_exe = entry.parent / "dist" / f"{name}.exe"
	if not dist_exe.exists():
		raise FileNotFoundError("Build completed but FRIDAY.exe was not found in dist/")
	print(f"[FRIDAY] Build complete: {dist_exe}")
	return dist_exe


def get_desktop_path() -> Path:
	userprofile = os.environ.get("USERPROFILE")
	if userprofile:
		p = Path(userprofile) / "Desktop"
		if p.exists():
			return p
	# Fallback to home/Desktop
	return Path.home() / "Desktop"


def get_startup_folder() -> Path:
	# %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
	appdata = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
	return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def create_shortcut(target: Path, shortcut_path: Path, icon: Path) -> None:
	try:
		import win32com.client  # type: ignore
		shell = win32com.client.Dispatch("WScript.Shell")
		shortcut = shell.CreateShortcut(str(shortcut_path))
		shortcut.TargetPath = str(target)
		shortcut.WorkingDirectory = str(target.parent)
		shortcut.IconLocation = str(icon)
		shortcut.Description = "FRIDAY – Personal AI Assistant"
		shortcut.Save()
		print(f"[FRIDAY] Shortcut created: {shortcut_path}")
	except Exception as ex:
		raise RuntimeError(f"Failed to create shortcut: {ex}")


def main() -> None:
	root = Path(__file__).resolve().parent
	entry = root / "main.py"
	icon = root / "friday.ico"
	if not entry.exists():
		raise FileNotFoundError("main.py not found in project root")
	if not icon.exists():
		print("[FRIDAY] Warning: friday.ico not found. Using default app icon.")

	# Ensure PyInstaller is available
	try:
		import PyInstaller  # type: ignore  # noqa: F401
	except Exception:
		print("[FRIDAY] Installing PyInstaller...")
		subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"]) 

	# Build
	exe_path = run_pyinstaller(entry=entry, icon=icon if icon.exists() else Path(""))

	# Create desktop shortcut
	desktop = get_desktop_path()
	desktop_shortcut = desktop / "FRIDAY.lnk"
	create_shortcut(exe_path, desktop_shortcut, icon if icon.exists() else exe_path)

	# Optional: add to Startup
	try:
		choice = input("Add FRIDAY to Startup (auto-launch on login)? [y/N]: ").strip().lower()
		if choice == "y":
			startup_folder = get_startup_folder()
			startup_shortcut = startup_folder / "FRIDAY.lnk"
			create_shortcut(exe_path, startup_shortcut, icon if icon.exists() else exe_path)
			print(f"[FRIDAY] Startup enabled at: {startup_shortcut}")
		else:
			print("[FRIDAY] Startup integration skipped.")
	except KeyboardInterrupt:
		print("\n[FRIDAY] Startup integration skipped by user.")

	print("[FRIDAY] All set, Boss. Your FRIDAY executable is mission-ready.")


if __name__ == "__main__":
	main()


