param([switch]$Draft, [string]$OutputName = '梯度_散度_旋度_配乐版.mp4', [string]$Python)
$ErrorActionPreference = 'Stop'
if ($Python) {
    $taskPython = $Python
} else {
    $taskPython = Join-Path $PSScriptRoot '..\..\.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $taskPython)) { $taskPython = 'python' }
}
Push-Location $PSScriptRoot
try {
    New-Item -ItemType Directory -Force -Path output | Out-Null
    if ($Draft) {
        & $taskPython -m manim -ql --progress_bar none vector_calculus.py VectorCalculus -o subtitle_animation_draft
        if ($LASTEXITCODE -ne 0) { throw 'Draft rendering failed.' }
        & $taskPython make_bgm.py --video 'media\videos\vector_calculus\480p15\subtitle_animation_draft.mp4' --output 'media\videos\vector_calculus\480p15\subtitle_animation_draft_bgm.mp4'
        if ($LASTEXITCODE -ne 0) { throw 'Background music generation failed.' }
        Copy-Item -LiteralPath 'media\videos\vector_calculus\480p15\subtitle_animation_draft_bgm.mp4' -Destination 'output\预览.mp4'
    } else {
        & $taskPython -m manim --resolution 1920,1080 --fps 24 --progress_bar none vector_calculus.py VectorCalculus -o subtitle_animation
        if ($LASTEXITCODE -ne 0) { throw 'Final rendering failed.' }
        & $taskPython make_bgm.py --video 'media\videos\vector_calculus\1080p24\subtitle_animation.mp4' --output 'media\videos\vector_calculus\1080p24\subtitle_animation_bgm.mp4'
        if ($LASTEXITCODE -ne 0) { throw 'Background music generation failed.' }
        $finalVideo = Join-Path 'output' $OutputName
        Copy-Item -LiteralPath 'media\videos\vector_calculus\1080p24\subtitle_animation_bgm.mp4' -Destination $finalVideo
        foreach ($legacyName in @('梯度_散度_旋度_字幕动画版.mp4', '梯度_散度_旋度_配乐版.mp4', '梯度_散度_旋度_科研简洁版.mp4', '梯度_散度_旋度_入门.mp4')) {
            if ($legacyName -eq $OutputName) { continue }
            try {
                Copy-Item -LiteralPath $finalVideo -Destination (Join-Path 'output' $legacyName)
            } catch [System.IO.IOException] {
                Write-Warning "Could not update legacy filename $legacyName because it is in use. The verified export is $finalVideo."
            }
        }
        & $taskPython -m manim -s --progress_bar none vector_calculus.py Cover
        if ($LASTEXITCODE -ne 0) { throw 'Cover rendering failed.' }
        Copy-Item -LiteralPath 'media\images\vector_calculus\Cover_ManimCE_v0.20.1.png' -Destination 'output\封面.png'
        & $taskPython verify_video.py --video $finalVideo
        if ($LASTEXITCODE -ne 0) { throw 'Video verification failed.' }
    }
} finally { Pop-Location }
