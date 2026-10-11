# Downloads Figma image renders to $env:TEMP\figma-images\.
# Usage: .\download-images.ps1 <name> <url> [<name> <url> ...]
#
# Example:
#   .\download-images.ps1 frame-01 "https://..." frame-02 "https://..."

param(
  [Parameter(ValueFromRemainingArguments)]
  [string[]]$Pairs
)

if ($Pairs.Count -lt 2 -or $Pairs.Count % 2 -ne 0) {
  Write-Error "Usage: download-images.ps1 <name> <url> [<name> <url> ...]"
  exit 1
}

$FigmaTmp = "$env:TEMP\figma-images"
New-Item -ItemType Directory -Force -Path $FigmaTmp | Out-Null

for ($i = 0; $i -lt $Pairs.Count; $i += 2) {
  $name = $Pairs[$i]
  $url  = $Pairs[$i + 1]
  Write-Host "Downloading $name..."
  Invoke-WebRequest -Uri $url -OutFile "$FigmaTmp\$name.png"
}

Write-Host "`nSaved to $FigmaTmp"
Get-ChildItem $FigmaTmp | Select-Object Name, Length
