$ErrorActionPreference='Stop'
$repo=Split-Path $PSScriptRoot -Parent
$output=Join-Path $repo 'bin\installer-tests'
New-Item -ItemType Directory -Force -Path $output | Out-Null
$compiler=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$executable=Join-Path $output 'InstallerTransactionTests.exe'
$sources=@((Join-Path $repo 'src\Installer.cs'),(Join-Path $PSScriptRoot 'InstallerTransactionTests.cs'))
& $compiler /nologo /noconfig /target:exe /optimize+ /r:System.dll /r:System.Core.dll /r:System.Windows.Forms.dll /r:System.Drawing.dll /main:InstallerTransactionTests ('/out:'+$executable) @sources
if($LASTEXITCODE -ne 0){throw 'Installer test build failed'}
& $executable
if($LASTEXITCODE -ne 0){throw 'Installer transaction test failed'}
