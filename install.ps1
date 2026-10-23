# Tilawa Studio - installation ou mise à jour en une ligne (Windows), à coller dans PowerShell :
# Tilawa Studio - one-line install or update (Windows), to paste in PowerShell:
#   irm https://raw.githubusercontent.com/oumarknt31/tilawa-studio/main/install.ps1 | iex
#
# Downloads the latest release (the app, ready to use: nothing to compile), checks it against the
# release's SHA256SUMS.txt, installs it for this user (no admin) in %LOCALAPPDATA%\Programs with
# Start menu and desktop shortcuts, gets the recitation model and the text drawing engine once,
# and starts it. Files downloaded by PowerShell carry no "downloaded from the internet" mark, so
# SmartScreen does not block the (not yet signed) app. Projects and videos are never touched.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'   # much faster downloads

function Say($fr, $en) { Write-Host ""; Write-Host "== $fr" -ForegroundColor Cyan; Write-Host "   $en" }
function Fail($fr, $en) { Write-Host ""; Write-Host "!! $fr" -ForegroundColor Red; Write-Host "   $en"; throw $en }

$base = if ($env:TILAWA_RELEASE_URL) { $env:TILAWA_RELEASE_URL } else {
    'https://github.com/oumarknt31/tilawa-studio/releases/latest/download' }
$root = if ($env:TILAWA_DEST) { $env:TILAWA_DEST } else { Join-Path $env:LOCALAPPDATA 'Programs' }
$file = 'TilawaStudio-Windows.zip'
if (-not [Environment]::Is64BitOperatingSystem) { Fail 'Tilawa Studio demande Windows 64 bits.' 'Tilawa Studio needs 64-bit Windows.' }

New-Item -ItemType Directory -Force -Path $root | Out-Null
$root = (Resolve-Path $root).Path
$dest = Join-Path $root 'Tilawa Studio'
$py = Join-Path $dest 'python\python.exe'
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('TilawaStudio-' + [guid]::NewGuid())
$staged = Join-Path $root '.Tilawa Studio-new'   # same drive as $dest: the swap is a rename
New-Item -ItemType Directory -Path $tmp | Out-Null

try {
    Say 'Téléchargement de Tilawa Studio (~600 Mo)...' 'Downloading Tilawa Studio (~600 MB)...'
    try {
        Invoke-WebRequest "$base/$file" -OutFile (Join-Path $tmp $file) -UseBasicParsing
        Invoke-WebRequest "$base/SHA256SUMS.txt" -OutFile (Join-Path $tmp 'SHA256SUMS.txt') -UseBasicParsing
    } catch {
        Fail 'Téléchargement impossible : vérifie ta connexion internet et réessaie.' 'Download failed: check your internet connection and try again.'
    }
    $line = Get-Content (Join-Path $tmp 'SHA256SUMS.txt') | Where-Object { ($_ -split '\s+')[1].TrimStart('*') -eq $file } | Select-Object -First 1
    $expected = if ($line) { ($line -split '\s+')[0] } else { '' }
    $actual = (Get-FileHash (Join-Path $tmp $file) -Algorithm SHA256).Hash
    if (-not $expected -or $expected -ne $actual) { Fail 'Le téléchargement est abîmé, réessaie.' 'The download is damaged, try again.' }

    Say 'Décompression...' 'Unpacking...'
    if (Test-Path $staged) { Remove-Item $staged -Recurse -Force }
    New-Item -ItemType Directory -Path $staged | Out-Null
    tar -xf (Join-Path $tmp $file) -C $staged   # much faster than Expand-Archive
    if ($LASTEXITCODE -ne 0) { Expand-Archive (Join-Path $tmp $file) -DestinationPath $staged -Force }
    if (-not (Test-Path (Join-Path $staged 'Tilawa Studio\python\python.exe'))) {
        Fail "Le téléchargement ne contient pas l'app." "The download doesn't contain the app."
    }

    # never close the app for the user: wait until it is closed
    $running = { Get-Process python, pythonw -EA SilentlyContinue | Where-Object { $_.Path -and $_.Path.StartsWith($dest) } }
    if (& $running) {
        Say 'Tilawa Studio est ouvert : ferme-le pour continuer. J''attends 3 minutes...' 'Tilawa Studio is open: close it to continue. Waiting 3 minutes...'
        $deadline = (Get-Date).AddSeconds(180)
        while (& $running) {
            if ((Get-Date) -gt $deadline) { Fail 'Tilawa Studio est encore ouvert. Ferme-le, puis relance cette commande.' 'Tilawa Studio is still open. Close it, then run this command again.' }
            Start-Sleep -Seconds 2
        }
    }

    Say "Installation dans $dest..." "Installing into $dest..."
    if (Test-Path "$dest.old") { Remove-Item "$dest.old" -Recurse -Force }
    if (Test-Path $dest) { Rename-Item $dest "$dest.old" }
    Move-Item (Join-Path $staged 'Tilawa Studio') $dest
    Remove-Item "$dest.old", $staged -Recurse -Force -EA SilentlyContinue

    # the window of the app is drawn by Microsoft Edge WebView2 (already there on most computers)
    $wv = 'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}'
    $hasWebView = (Test-Path "HKLM:\$wv") -or (Test-Path ("HKCU:\" + $wv.Replace('WOW6432Node\', '')))
    if (-not $hasWebView) {
        Say 'Installation de Microsoft WebView2 (pour la fenêtre de l''app)...' 'Installing Microsoft WebView2 (for the app window)...'
        $wvi = Join-Path $tmp 'webview2.exe'
        Invoke-WebRequest 'https://go.microsoft.com/fwlink/p/?LinkId=2124703' -OutFile $wvi -UseBasicParsing
        Start-Process $wvi -ArgumentList '/silent', '/install' -Wait
    }

    & $py -m tilawa.shortcuts | Out-Null
    if (-not $env:TILAWA_NO_SETUP) {
        Say 'Modèle de reconnaissance et moteur du texte (une seule fois, ~1,3 Go)...' 'Recognition model and text engine (once, ~1.3 GB)...'
        & $py -m tilawa.cli setup
        if ($LASTEXITCODE -ne 0) { Fail 'La préparation a échoué : relance cette commande.' 'Setup failed: run this command again.' }
    }
    Say 'Tilawa Studio est installé : il est dans le menu Démarrer et sur le bureau.' 'Tilawa Studio is installed: it is in the Start menu and on the desktop.'
    if (-not $env:TILAWA_NO_OPEN) {
        Start-Process (Join-Path $dest 'python\pythonw.exe') -ArgumentList '-m', 'tilawa.cli', 'desktop' -WorkingDirectory $dest
    }
} finally {
    Remove-Item $tmp -Recurse -Force -EA SilentlyContinue
}
