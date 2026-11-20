# 이미지 생성 라이브러리 (PowerShell + System.Drawing)
# 용도: 투자 전략 리포트(index.html)에서 참조하는 차트 2장 제작
# 실행: powershell -ExecutionPolicy Bypass -File make-images.ps1
#
# 주의: [Drawing.Color]::FromArgb(...) 를 함수 인자 자리에 직접 쓰지 말 것.
#       반드시 변수에 담아서 넘긴다.

param([string]$OutDir = "")

Add-Type -AssemblyName System.Drawing

if (-not $OutDir) { $OutDir = Join-Path $PSScriptRoot "images" }
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }

# ── 테마 ───────────────────────────────────────────────────────
$ACCENT = [Drawing.Color]::FromArgb(37, 99, 235)
$DARK   = [Drawing.Color]::FromArgb(17, 24, 39)
$GRAY   = [Drawing.Color]::FromArgb(107, 114, 128)
$LGRAY  = [Drawing.Color]::FromArgb(243, 244, 246)
$BORDER = [Drawing.Color]::FromArgb(203, 213, 225)
$ORANGE = [Drawing.Color]::FromArgb(217, 119, 6)
$WHITE  = [Drawing.Color]::White
$AXIS   = [Drawing.Color]::FromArgb(229, 231, 235)

function New-C {
  param($w, $h, $bg)
  $bmp = New-Object Drawing.Bitmap($w, $h)
  $g = [Drawing.Graphics]::FromImage($bmp)
  $g.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias
  $g.TextRenderingHint = [Drawing.Text.TextRenderingHint]::AntiAliasGridFit
  $g.Clear($bg)
  return @($bmp, $g)
}

function New-Font {
  param($size, $bold)
  $style = [Drawing.FontStyle]::Regular
  if ($bold) { $style = [Drawing.FontStyle]::Bold }
  return New-Object Drawing.Font("Malgun Gothic", $size, $style, [Drawing.GraphicsUnit]::Pixel)
}

function Draw-Str {
  param($g, $text, $x, $y, $w, $h, $size, $bold, $color, $align)
  $f = New-Font $size $bold
  $b = New-Object Drawing.SolidBrush($color)
  $sf = New-Object Drawing.StringFormat
  $sf.Alignment = $align
  $sf.LineAlignment = [Drawing.StringAlignment]::Near
  $sf.Trimming = [Drawing.StringTrimming]::Word
  $g.DrawString($text, $f, $b, (New-Object Drawing.RectangleF($x, $y, $w, $h)), $sf)
  $f.Dispose(); $b.Dispose(); $sf.Dispose()
}

function Draw-Bar {
  param($g, $x, $y, $w, $h, $color)
  $b = New-Object Drawing.SolidBrush($color)
  $g.FillRectangle($b, $x, $y, $w, $h)
  $b.Dispose()
}

# ═══════════════════════════════════════════════════════════════
# 01. ETF vs 개별주 실적 비교 (800x400)
# ═══════════════════════════════════════════════════════════════
$c = New-C 800 400 $WHITE
$bmp = $c[0]; $g = $c[1]

Draw-Str $g "ETF vs 개별주 연간 수익률 (%)" 30 22 500 34 22 $true $DARK ([Drawing.StringAlignment]::Near)
Draw-Str $g "출처: 투자 전략 리포트 2026-11-07" 30 56 500 20 14 $false $GRAY ([Drawing.StringAlignment]::Near)

# 범례
Draw-Bar $g 580 30 14 14 $ACCENT
Draw-Str $g "ETF" 600 27 60 20 15 $false $DARK ([Drawing.StringAlignment]::Near)
Draw-Bar $g 670 30 14 14 $ORANGE
Draw-Str $g "개별주" 690 27 90 20 15 $false $DARK ([Drawing.StringAlignment]::Near)

$baseY = 330
$topY  = 120
$maxV  = 35.0
$span  = $baseY - $topY

# 눈금선 / y축 라벨
foreach ($v in 0, 10, 20, 30) {
  $yy = $baseY - [int](($v / $maxV) * $span)
  $pen = New-Object Drawing.Pen($AXIS, 1)
  $g.DrawLine($pen, 66, $yy, 760, $yy)
  $pen.Dispose()
  Draw-Str $g "$v" 30 ($yy - 9) 30 20 14 $false $GRAY ([Drawing.StringAlignment]::Far)
}

# x축
$axisPen = New-Object Drawing.Pen($BORDER, 1)
$g.DrawLine($axisPen, 66, $baseY, 760, $baseY)
$axisPen.Dispose()

$groups = @(
  @("2023", 23.1, 31.5),
  @("2024", 14.8, 9.2),
  @("2025", 8.5, 12.3)
)

$groupW = 694 / 3
for ($i = 0; $i -lt $groups.Count; $i++) {
  $gp = $groups[$i]
  $center = 66 + ($groupW * $i) + ($groupW / 2)
  $barW = 62

  # ETF
  $h1 = [int](($gp[1] / $maxV) * $span)
  $x1 = [int]($center - $barW - 6)
  Draw-Bar $g $x1 ($baseY - $h1) $barW $h1 $ACCENT
  Draw-Str $g ("+{0:N1}%" -f $gp[1]) $x1 ($baseY - $h1 - 24) $barW 20 15 $true $ACCENT ([Drawing.StringAlignment]::Center)

  # 개별주
  $h2 = [int](($gp[2] / $maxV) * $span)
  $x2 = [int]($center + 6)
  Draw-Bar $g $x2 ($baseY - $h2) $barW $h2 $ORANGE
  Draw-Str $g ("+{0:N1}%" -f $gp[2]) $x2 ($baseY - $h2 - 24) $barW 20 15 $true $ORANGE ([Drawing.StringAlignment]::Center)

  Draw-Str $g $gp[0] ([int]($center - 40)) ($baseY + 10) 80 22 17 $true $DARK ([Drawing.StringAlignment]::Center)
}

$bmp.Save("$OutDir\etf_comparison.png", [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()

# ═══════════════════════════════════════════════════════════════
# 02. 2026년 1월 리스크 타임라인 (800x300)
# ═══════════════════════════════════════════════════════════════
$c = New-C 800 300 $WHITE
$bmp = $c[0]; $g = $c[1]

Draw-Str $g "2026년 1월 리스크 타임라인" 30 22 600 34 22 $true $DARK ([Drawing.StringAlignment]::Near)
Draw-Str $g "본문 '행동 요령' 기준" 30 56 600 20 14 $false $GRAY ([Drawing.StringAlignment]::Near)

$axisY = 176
$pen = New-Object Drawing.Pen($BORDER, 3)
$g.DrawLine($pen, 70, $axisY, 740, $axisY)
$pen.Dispose()

$nodes = @(
  @("1월 초", "포트폴리오 재검토", "매월 1일 / 매년 1월"),
  @("상시", "변동성 모니터링", "달러·금·방어주 10~15%"),
  @("이벤트 시", "AI·반도체 뉴스 대응", "급등 후 개별주 청산 검토")
)

$nodeW = 660 / 3
for ($i = 0; $i -lt $nodes.Count; $i++) {
  $n = $nodes[$i]
  $cx = [int](70 + ($nodeW * $i) + ($nodeW / 2))

  $dot = New-Object Drawing.SolidBrush($ACCENT)
  $g.FillEllipse($dot, ($cx - 9), ($axisY - 9), 18, 18)
  $dot.Dispose()
  $ring = New-Object Drawing.Pen($WHITE, 3)
  $g.DrawEllipse($ring, ($cx - 9), ($axisY - 9), 18, 18)
  $ring.Dispose()

  Draw-Str $g $n[0] ($cx - 100) 96 200 24 14 $true $GRAY ([Drawing.StringAlignment]::Center)
  Draw-Str $g $n[1] ($cx - 100) 118 200 26 18 $true $DARK ([Drawing.StringAlignment]::Center)

  Draw-Str $g $n[2] ($cx - 105) ($axisY + 22) 210 40 14 $false $GRAY ([Drawing.StringAlignment]::Center)
}

$bmp.Save("$OutDir\risk_timeline.png", [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()

Write-Output "DONE"
Get-ChildItem $OutDir | Select-Object Name, Length | Format-Table -AutoSize
