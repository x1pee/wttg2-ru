param([Parameter(Mandatory=$true)][string]$GamePath,[string]$OutputPath="$PSScriptRoot\bin")
$ErrorActionPreference='Stop'
$managed=Join-Path $GamePath 'WTTG2_Data\Managed'
$compiler=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
New-Item -ItemType Directory -Force -Path $OutputPath | Out-Null
$refs=@('mscorlib.dll','System.dll','UnityEngine.dll','UnityEngine.CoreModule.dll','UnityEngine.AudioModule.dll','UnityEngine.UIModule.dll','UnityEngine.UI.dll','UnityEngine.TextRenderingModule.dll','UnityEngine.VideoModule.dll','UnityEngine.ScreenCaptureModule.dll','TextMeshPro-2017.3-1.0.56-Runtime.dll') | ForEach-Object {'/r:'+(Join-Path $managed $_)}
& $compiler /nologo /noconfig /nostdlib+ /target:library /optimize+ ('/out:'+(Join-Path $OutputPath 'WTTG2RU.dll')) @refs (Join-Path $PSScriptRoot 'src\RuRuntime.cs')
if($LASTEXITCODE -ne 0){throw 'Subtitle runtime build failed'}
& $compiler /nologo /noconfig /target:winexe /optimize+ /r:System.dll /r:System.Core.dll /r:System.Windows.Forms.dll /r:System.Drawing.dll ('/out:'+(Join-Path $OutputPath 'WTTG2-RU-Setup.exe')) (Join-Path $PSScriptRoot 'src\Installer.cs')
if($LASTEXITCODE -ne 0){throw 'Installer build failed'}
