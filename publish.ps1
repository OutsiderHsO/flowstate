# publish.ps1 — lint, build, and (optionally) push a post to the live site.
#
# The everyday loop:
#   1. .\publish.ps1                 -> check + build locally, nothing published
#   2. .\publish.ps1 -Push           -> check + build + commit + push (live)
#
# Why a script: this machine has no Node/pnpm/git on PATH, so the commands
# need absolute paths. Doing it here means you cannot forget a step and
# publish a broken page.

param(
  [switch]$Push,
  [string]$Message = ''
)

$ErrorActionPreference = 'Stop'

$Root       = Split-Path -Parent $MyInvocation.MyCommand.Path
$Node       = 'C:\Users\admin\.dsh\dsh-runtimes\dsh-next-primary-runtime\dependencies\node\bin\node.exe'
$Python     = 'C:\Users\admin\.dsh\dsh-runtimes\dsh-next-primary-runtime\dependencies\python\python.exe'
$Git        = 'C:\Users\admin\.tools\git\cmd\git.exe'
$Astro      = Join-Path $Root 'node_modules\astro\bin\astro.mjs'

$env:ASTRO_TELEMETRY_DISABLED = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

# This network cannot reach github.com:443, but ssh.github.com:443 answers.
# ~/.ssh/config maps github.com onto that endpoint, and we give Git a
# non-interactive SSH command so a prompt can never hang the script.
$env:GIT_SSH_COMMAND = 'ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 -o BatchMode=yes'

Set-Location -LiteralPath $Root

function Step($text) {
  Write-Host ''
  Write-Host "== $text" -ForegroundColor Cyan
}

# ---------------------------------------------------------------- 1. lint
Step 'Checking posts (frontmatter, duplicates, encoding)'
& $Python (Join-Path $Root 'scripts\newpost.py') lint
if ($LASTEXITCODE -ne 0) {
  Write-Host ''
  Write-Host 'Lint failed — nothing was built or published.' -ForegroundColor Red
  exit 1
}

# ------------------------------------------------------------ 2. preflight
# Only meaningful when we are about to push: a cloud build runs in a clean
# checkout, so a missing packageManager or a dirty tree matters then.
if ($Push) {
  Step 'Preflight (will this build on Cloudflare?)'
  & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'preflight.ps1')
  if ($LASTEXITCODE -ne 0) {
    Write-Host ''
    Write-Host 'Preflight found blocking problems — nothing was published.' -ForegroundColor Red
    exit 1
  }
}

# --------------------------------------------------------------- 3. build
Step 'Building the site'
& $Node $Astro build
if ($LASTEXITCODE -ne 0) {
  Write-Host ''
  Write-Host 'Build failed — nothing was published.' -ForegroundColor Red
  exit 1
}

# ------------------------------------------------------------- 3. drafts
$drafts = Get-ChildItem -Path (Join-Path $Root 'src\content') -Recurse -Filter *.md |
  Where-Object { (Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8) -match '(?m)^draft:\s*true' }
if ($drafts) {
  Write-Host ''
  Write-Host "Still marked draft: true (not published):" -ForegroundColor Yellow
  $drafts | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Yellow }
}

if (-not $Push) {
  Write-Host ''
  Write-Host 'Everything built fine. Nothing was published.' -ForegroundColor Green
  Write-Host 'To preview:  powershell -NoProfile -ExecutionPolicy Bypass -File ".\dev.ps1" preview'
  Write-Host 'To publish:  .\publish.ps1 -Push'
  exit 0
}

# ------------------------------------------------------------ 4. git push
Step 'Publishing to GitHub'
& $Git add -A
& $Git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
  Write-Host 'No content changes to publish.' -ForegroundColor Green
  exit 0
}

if (-not $Message) {
  $Message = "content: update $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
}

& $Git commit -m $Message
if ($LASTEXITCODE -ne 0) {
  Write-Host 'Commit failed.' -ForegroundColor Red
  exit 1
}

$remote = & $Git remote
if (-not $remote) {
  Write-Host ''
  Write-Host 'Committed locally, but no GitHub remote is configured yet.' -ForegroundColor Yellow
  Write-Host 'Create the repo, then run:' -ForegroundColor Yellow
  Write-Host '  & "' + $Git + '" remote add origin https://github.com/<你的用户名>/<仓库名>.git'
  Write-Host '  & "' + $Git + '" push -u origin main'
  exit 1
}

& $Git push
if ($LASTEXITCODE -ne 0) {
  Write-Host 'Push failed — check your network or GitHub credentials.' -ForegroundColor Red
  exit 1
}

Write-Host ''
Write-Host 'Pushed. GitHub Actions / Cloudflare will rebuild the site in about a minute.' -ForegroundColor Green
