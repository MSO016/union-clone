# Batch decompile dos .pyc DECIFRADOS (PYEN -> py3.13), preservando estrutura.
param(
  [string]$src = "D:\MSO\Projects\union-clone\decrypted",
  [string]$out = "D:\MSO\Projects\union-clone\decomp-decrypted"
)
$pycdc = "D:\MSO\Projects\union-clone\tools\pycdc-new.exe"

$files = Get-ChildItem -Recurse -File $src -Filter *.pyc
Write-Output "alvos: $($files.Count)"
$ok = 0; $fail = 0; $partial = 0
$failList = @()

foreach ($f in $files) {
  $rel = $f.FullName.Substring($src.Length + 1)
  $dest = Join-Path $out ($rel -replace '\.pyc$', '.py')
  $destDir = Split-Path $dest -Parent
  if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
  $all = (& $pycdc $f.FullName 2>&1 | ForEach-Object { $_.ToString() }) -join "`n"
  $incomplete = ($all -match 'incomplete|Unsupported opcode|WARNING')
  $clean = (($all -split "`n" | Where-Object { $_ -notmatch 'WARNING: decompilation incomplete|Unsupported opcode:|^\(Python 3\.\d+\)$|^\s*$' }) -join "`n")
  if ([string]::IsNullOrWhiteSpace($clean)) { $fail++; $failList += $rel; continue }
  Set-Content -Path $dest -Value $clean -Encoding utf8
  if ($incomplete) { $partial++ } else { $ok++ }
}
Write-Output "ok=$ok  parcial=$partial  falhou=$fail"
if ($failList.Count) { Write-Output "FALHOS:"; $failList | ForEach-Object { Write-Output "  $_" } }
