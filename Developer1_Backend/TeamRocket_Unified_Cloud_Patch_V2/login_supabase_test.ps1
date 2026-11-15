# Run in the SAME PowerShell terminal where you start the backend.
# Requires $env:SUPABASE_URL and $env:SUPABASE_ANON_KEY (publishable/anon key, not secret role key).
param([Parameter(Mandatory=$true)][string]$Email)
$ErrorActionPreference='Stop'
if (-not $env:SUPABASE_URL -or -not $env:SUPABASE_ANON_KEY) { throw 'Set SUPABASE_URL and SUPABASE_ANON_KEY first.' }
if ($env:SUPABASE_URL -notmatch '^https://[a-z0-9-]+\.supabase\.co/?$') { throw 'Check SUPABASE_URL: expected https://PROJECT.supabase.co' }
if ($env:SUPABASE_ANON_KEY -match '^sb_secret_') { throw 'Use publishable/anon key here, never an sb_secret_ key.' }
$pw = Read-Host 'Supabase test-user password (not your database secret key)' -AsSecureString
$plain = [System.Net.NetworkCredential]::new('', $pw).Password
try {
    $json = @{email=$Email; password=$plain} | ConvertTo-Json -Compress
    $login = Invoke-RestMethod -Uri ($env:SUPABASE_URL.TrimEnd('/')+'/auth/v1/token?grant_type=password') `
       -Method Post -Headers @{apikey=$env:SUPABASE_ANON_KEY} -ContentType 'application/json' -Body $json
    if (-not $login.access_token) { throw 'Login returned no access_token' }
    $env:SYNC_ACCESS_TOKEN = $login.access_token
    $env:SYNC_RPC_URL = $env:SUPABASE_URL.TrimEnd('/')+'/rest/v1/rpc/ingest_sync_event'
    Write-Host 'Authenticated test JWT loaded into THIS terminal (token not printed).'
    Write-Host 'Start backend from this terminal. Refresh the JWT by rerunning this script after expiry.'
} finally { Remove-Variable plain,json,login -ErrorAction SilentlyContinue }
