# dev.ps1 — one-shot local development launcher for automotive-journal
#
# Why this exists: this machine has no Node/pnpm/git on PATH. They live in
# DSH's bundled runtime instead, so plain `pnpm dev` fails with
# "pnpm is not recognized". Run this file instead:
#
#     .\dev.ps1          # start the dev server at http://localhost:4321
#     .\dev.ps1 build    # production build into dist\
#     .\dev.ps1 preview  # serve the built dist\ locally
#
# Add -NoSandboxFriendly only if you need it; nothing here changes global
# settings, PATH or installs anything.

param(
  [ValidateSet('dev', 'build', 'preview', 'install')]
  [string]$Task = 'dev'
)

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

$Node = 'C:\Users\admin\.dsh\dsh-runtimes\dsh-next-primary-runtime\dependencies\node\bin\node.exe'
$Pnpm = 'C:\Users\admin\.dsh\dsh-runtimes\dsh-next-primary-runtime\dependencies\pnpm\bin\pnpm.mjs'
$Astro = Join-Path $ProjectRoot 'node_modules\astro\bin\astro.mjs'

# Astro telemetry writes to %APPDATA% and is unnecessary for a personal site.
$env:ASTRO_TELEMETRY_DISABLED = '1'

if (-not (Test-Path -LiteralPath $Node)) {
  Write-Host "Node runtime not found at:`n  $Node" -ForegroundColor Red
  Write-Host 'Re-run load_workspace_dependencies in DSH, or install Node 22+ and edit the paths in dev.ps1.'
  exit 1
}

Set-Location -LiteralPath $ProjectRoot

switch ($Task) {
  'install' {
    & $Node $Pnpm install --no-frozen-lockfile
  }
  'build' {
    & $Node $Astro build
  }
  'preview' {
    & $Node $Astro preview --port 4321 --host 127.0.0.1
  }
  default {
    Write-Host 'Starting dev server... open http://localhost:4321 (Ctrl+C to stop)' -ForegroundColor Cyan
    # --host 127.0.0.1 pins IPv4. Without it Astro binds only [::1] on Windows,
    # so tools that resolve to 127.0.0.1 fail to connect.
    & $Node $Astro dev --port 4321 --host 127.0.0.1
  }
}

exit $LASTEXITCODE
