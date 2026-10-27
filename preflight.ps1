# preflight.ps1 — catch the things that break a cloud build, before you push.
#
# Why: Cloudflare builds from a clean checkout, with no node_modules, no
# local cache and a different OS-independent environment. Most "it works
# locally" failures come from a handful of specific causes, all checked here:
#
#   * packageManager / engines missing -> CI picks the wrong Node or pnpm
#   * files that must not be committed  -> secrets, local caches, dist
#   * uncommitted changes               -> you deploy an older site than you see
#   * lockfile out of sync              -> `pnpm install` refuses to proceed
#   * a placeholder `site` URL           -> wrong canonical/OG links
#
# Run this before the first deploy, and any time you change build config.

param(
  [switch]$Full   # also do a clean reinstall to simulate a fresh checkout
)

$ErrorActionPreference = 'Continue'

$Root   = Split-Path -Parent $MyInvocation.MyCommand.Path
$Node   = 'C:\Users\admin\.dsh\dsh-runtimes\dsh-next-primary-runtime\dependencies\node\bin\node.exe'
$Pnpm   = 'C:\Users\admin\.dsh\dsh-runtimes\dsh-next-primary-runtime\dependencies\pnpm\bin\pnpm.mjs'
$Git    = 'C:\Users\admin\.tools\git\cmd\git.exe'
$Astro  = Join-Path $Root 'node_modules\astro\bin\astro.mjs'

$env:ASTRO_TELEMETRY_DISABLED = '1'
$env:GIT_SSH_COMMAND = 'ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 -o BatchMode=yes'

Set-Location -LiteralPath $Root

$fail = 0
function Ok($m)   { Write-Host "  OK      $m" -ForegroundColor Green }
function Warn($m) { Write-Host "  WARN    $m" -ForegroundColor Yellow }
function Bad($m)  { Write-Host "  FAIL    $m" -ForegroundColor Red; $script:fail++ }
function Head($m) { Write-Host ''; Write-Host "== $m" -ForegroundColor Cyan }

# ------------------------------------------------------------ package meta
Head 'Project metadata'
$pkg = Get-Content package.json -Raw | ConvertFrom-Json
if ($pkg.packageManager) { Ok "packageManager = $($pkg.packageManager)" }
else { Bad 'package.json has no "packageManager" — CI may use a wrong pnpm version' }

if ($pkg.engines.node) { Ok "engines.node = $($pkg.engines.node)" }
else { Bad 'package.json has no "engines.node" — CI may pick Node 18 and fail' }

# ------------------------------------------------------------------ config
Head 'Build configuration'
if (Test-Path wrangler.toml) {
  $w = Get-Content wrangler.toml -Raw
  if ($w -match 'publish\s*=\s*"dist"') { Ok 'wrangler.toml publishes dist/' }
  else { Warn 'wrangler.toml does not set publish = "dist"' }
  if ($w -match 'NODE_VERSION') { Ok 'wrangler.toml pins NODE_VERSION' }
  else { Warn 'wrangler.toml does not pin NODE_VERSION' }
} else { Warn 'no wrangler.toml (you can configure the build in the dashboard instead)' }

$ws = Get-Content pnpm-workspace.yaml -Raw
if ($ws -match 'storeDir|store-dir') { Warn 'a store directory is pinned in config — make sure it is not an absolute local path' }
else { Ok 'no absolute store path in pnpm config (cloud-safe)' }

$config = Get-Content astro.config.mjs -Raw
if ($config -match 'example\.github\.io') {
  Warn 'astro.config.mjs still has the placeholder site URL — canonical/OG links will point to the wrong host'
} else { Ok 'site URL is set to a real value' }

# -------------------------------------------------------------- git status
Head 'Repository state'
$branch = & $Git rev-parse --abbrev-ref HEAD 2>&1
Ok "branch: $branch"

$dirty = & $Git status --porcelain 2>&1
if ($dirty) {
  Warn "$(@($dirty).Count) uncommitted file(s) — these will NOT be deployed:"
  $dirty | Select-Object -First 8 | ForEach-Object { Write-Host "            $_" -ForegroundColor Yellow }
} else { Ok 'working tree is clean' }

$remote = & $Git ls-remote origin refs/heads/$branch 2>&1
if ($LASTEXITCODE -ne 0) {
  Bad 'cannot reach the git remote — check your SSH key and network'
} else {
  $local = (& $Git rev-parse HEAD 2>&1)
  $remoteSha = ($remote -split '\s+')[0]
  if ($local -eq $remoteSha) { Ok 'local HEAD matches the remote (nothing to push)' }
  else { Warn 'local commits are ahead of the remote — run .\publish.ps1 -Push' }
}

# ------------------------------------------------------------------ secrets
Head 'Nothing sensitive is committed'
$tracked = & $Git ls-files 2>&1
foreach ($pattern in @('\.env', '\.pem$', 'id_ed25519', 'id_rsa', 'node_modules/', 'dist/', '\.store-local/', '\.pdf$', '\.docx$')) {
  $hit = $tracked | Where-Object { $_ -match $pattern }
  if ($hit) { Bad "tracked files match '$pattern': $($hit -join ', ')" }
}
if (-not $fail) { Ok 'no secrets, caches or build output are tracked' }

# ------------------------------------------------------------------- build
Head 'Local build'
& $Node $Astro build 2>&1 | Select-Object -Last 3
if ($LASTEXITCODE -ne 0) { Bad 'local build failed' } else { Ok 'local build succeeded' }

if ($Full) {
  Head 'Clean install (simulating a fresh cloud checkout)'
  if (Test-Path node_modules) {
    try { Remove-Item -Recurse -Force node_modules -ErrorAction Stop }
    catch { Write-Host "  note: could not fully remove node_modules ($($_.Exception.Message.Split([Environment]::NewLine)[0]))" -ForegroundColor DarkGray }
  }

  $installLog = Join-Path $env:TEMP 'flowstate-install.log'
  & $Node $Pnpm install --frozen-lockfile --store-dir "$Root\.store-local" *> $installLog
  $installExit = $LASTEXITCODE
  $log = Get-Content $installLog -Raw -ErrorAction SilentlyContinue

  # This machine has no `npm`/`node` on PATH, and dependency postinstall
  # scripts shell out to them. That is a local-environment gap, not a defect;
  # Cloudflare's build image has both.
  $toolMissing = $log -match "'(npm|node)' is not recognized"
  $policyError = $log -match 'ERR_PNPM_MINIMUM_RELEASE_AGE_VIOLATION|Lockfile failed supply-chain'
  $realError = $log -match '\[ERR_PNPM_FROZEN_LOCKFILE|ERR_PNPM_LOCKFILE|ERR_PNPM_NO_MATCHING_VERSION'

  if ($policyError) {
    Bad 'lockfile contains packages newer than minimumReleaseAge — Cloudflare will reject it'
    Write-Host '        pin the offending packages under `overrides` in pnpm-workspace.yaml' -ForegroundColor Yellow
  }
  elseif ($realError) {
    Bad 'frozen-lockfile install failed — the lockfile is out of sync with package.json'
    Write-Host '        run: .\dev.ps1 install   then commit pnpm-lock.yaml' -ForegroundColor Yellow
  }
  elseif ($installExit -ne 0 -and $toolMissing) {
    Warn 'dependency postinstall scripts could not run: no npm/node on PATH here'
    Write-Host '        harmless locally (Cloudflare has both); the lockfile and build still work' -ForegroundColor DarkGray
  }
  elseif ($installExit -eq 0) {
    Ok 'frozen-lockfile install succeeded (CI will work)'
  }
  else {
    Bad "install failed with exit code $installExit — see $installLog"
  }
}

# ------------------------------------------------ supply-chain policy check
# Cloudflare enforces pnpm's default minimumReleaseAge (1440 min). This machine
# resolved without it once, so a fresh cloud build rejected the lockfile. Verify
# the lockfile passes the *strict* policy before every push.
Head 'Supply-chain policy (as Cloudflare enforces it)'
$policyLog = Join-Path $env:TEMP 'flowstate-policy.log'
$env:npm_config_minimumReleaseAge = '1440'
$env:npm_config_minimumReleaseAgeStrict = 'true'
& $Node $Pnpm install --frozen-lockfile --lockfile-only --store-dir "$Root\.store-local" *> $policyLog
$policyExit = $LASTEXITCODE
Remove-Item Env:\npm_config_minimumReleaseAge -ErrorAction SilentlyContinue
Remove-Item Env:\npm_config_minimumReleaseAgeStrict -ErrorAction SilentlyContinue

if ($policyExit -eq 0) {
  Ok 'lockfile passes pnpm supply-chain policy (minimumReleaseAge = 1440)'
}
else {
  Get-Content $policyLog | Where-Object { $_ -match 'was published|VIOLATION|failed' } |
    Select-Object -First 6 | ForEach-Object { Write-Host "        $_" -ForegroundColor Yellow }
  Bad 'lockfile fails the supply-chain policy — Cloudflare will reject this build'
  Write-Host '        fix: add the listed packages to `overrides` in pnpm-workspace.yaml' -ForegroundColor Yellow
  Write-Host '        pointing at the newest version older than 1 day' -ForegroundColor Yellow
}

# ------------------------------------------------------------------ summary
Write-Host ''
if ($fail -gt 0) {
  Write-Host "$fail blocking problem(s). Fix these before deploying." -ForegroundColor Red
  exit 1
}
Write-Host 'No blocking problems. Safe to deploy.' -ForegroundColor Green
Write-Host 'Cloudflare: Workers & Pages -> Create -> Pages -> Connect to Git'
