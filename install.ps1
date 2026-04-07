param(
  [string]$CodexHome,
  [switch]$Force
)

$scriptPath = Join-Path $PSScriptRoot 'scripts\install_to_codex_skills.py'
$args = @($scriptPath)

if ($CodexHome) {
  $args += @('--codex-home', $CodexHome)
}

if ($Force) {
  $args += '--force'
}

python @args
