# post.ps1 — the authoring command, without needing Python on PATH.
#
# This machine has no `python` on PATH (the interpreter ships inside DSH's
# bundled runtime), so `python scripts/newpost.py ...` fails with
# "'python' is not recognized". This wrapper uses the absolute path and
# forwards every argument unchanged.
#
# Examples:
#   .\post.ps1 new --track fiction --type shortstory --lang zh --title "新短篇"
#   .\post.ps1 list
#   .\post.ps1 edit my-story --dek "一句话简介" --rating T
#   .\post.ps1 publish my-story
#   .\post.ps1 lint
#
# If you later install Python properly, you can keep using this script or
# swap to `python scripts/newpost.py ...` directly — both do the same thing.

$ErrorActionPreference = 'Stop'

$Root   = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = 'C:\Users\admin\.dsh\dsh-runtimes\dsh-next-primary-runtime\dependencies\python\python.exe'
$Tool   = Join-Path $Root 'scripts\newpost.py'

if (-not (Test-Path -LiteralPath $Python)) {
  Write-Host 'Bundled Python not found at:' -ForegroundColor Red
  Write-Host "  $Python"
  Write-Host 'Either restore the DSH runtime, or install Python 3.10+ and edit $Python in this file.'
  exit 1
}

# Force UTF-8 so Chinese titles are not mangled by the console code page.
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

& $Python $Tool @args
exit $LASTEXITCODE
