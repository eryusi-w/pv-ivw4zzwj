# 이미지 생성 라이브러리 (PowerShell + System.Drawing)
# 용도: 네이버 블로그용 1200x675 PNG 5장 제작
# 실행: UTF-8 BOM으로 저장 후  powershell -ExecutionPolicy Bypass -File make-images.ps1
#
# 주의: [Drawing.Color]::FromArgb(...) 를 함수 인자 자리에 직접 쓰지 말 것.
#       반드시 변수에 담아서 넘긴다. (직접 쓰면 문자열로 전달되어 도형이 그려지지 않음)

param([string]$OutDir = "")

Add-Type -AssemblyName System.Drawing

# 출력 폴더: 인자 > 스크립트 옆 images\
if (-not $OutDir) { $OutDir = Join-Path $PSScriptRoot "images" }
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }

# ── 테마 (네이버 블로그 분위기, 서스테인블한 디자인) ───────────────────
$ACCENT = [Drawing.Color]::FromArgb(91, 87, 214)   # Indigo 600 - 차분한 파란색
$DARK   = [Drawing.Color]::FromArgb(30, 30, 36)    # Charcoal - 읽기 쎄한 다크
$GRAY   = [Drawing.Color]::FromArgb(94, 101, 115)   # Gray 600 - 중립 회색
$LGRAY  = [Drawing.Color]::FromArgb(248, 250, 252)  # Gray 100 - 부드러운 배경
$BORDER = [Drawing.Color]::FromArgb(228, 230, 236) # Gray 300 - 부드러운 테두리
$GREEN  = [Drawing.Color]::FromArgb(16, 185, 129)   # Emerald 500 - 성공 의미
$ORANGE = [Drawing.Color]::FromArgb(245, 158, 11)   # Amber 500 - 경고 의미
$WHITE  = [Drawing.Color]::White

$W = 1200; $H = 675
$HeaderTitle = "Orkas"
$HeaderRight = "local-first"

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

function New-Mono {
  param($size, $bold)
  $style = [Drawing.FontStyle]::Regular
  if ($bold) { $style = [Drawing.FontStyle]::Bold }
  return New-Object Drawing.Font("Consolas", $size, $style, [Drawing.GraphicsUnit]::Pixel)
}

function New-RoundedPath {
  param($x, $y, $w, $h, $r)
  $p = New-Object Drawing.Drawing2D.GraphicsPath
  $d = $r * 2
  $p.AddArc($x, $y, $d, $d, 180, 90)
  $p.AddArc($x + $w - $d, $y, $d, $d, 270, 90)
  $p.AddArc($x + $w - $d, $y + $h - $d, $d, $d, 0, 90)
  $p.AddArc($x, $y + $h - $d, $d, $d, 90, 90)
  $p.CloseFigure()
  return $p
}

function Draw-RoundBox {
  param($g, $x, $y, $w, $h, $r, $fill, $line, $lineW)
  $p = New-RoundedPath $x $y $w $h $r
  $b = New-Object Drawing.SolidBrush($fill)
  $g.FillPath($b, $p)
  $b.Dispose()
  if ($null -ne $line) {
    $pen = New-Object Drawing.Pen($line, $lineW)
    $g.DrawPath($pen, $p)
    $pen.Dispose()
  }
  $p.Dispose()
}

function Draw-DashBox {
  param($g, $x, $y, $w, $h, $r, $fill, $line, $lineW)
  $p = New-RoundedPath $x $y $w $h $r
  $b = New-Object Drawing.SolidBrush($fill)
  $g.FillPath($b, $p)
  $b.Dispose()
  $pen = New-Object Drawing.Pen($line, $lineW)
  $pen.DashStyle = [Drawing.Drawing2D.DashStyle]::Dash
  $g.DrawPath($pen, $p)
  $pen.Dispose(); $p.Dispose()
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

function Draw-MonoStr {
  param($g, $text, $x, $y, $w, $h, $size, $color)
  $f = New-Mono $size $false
  $b = New-Object Drawing.SolidBrush($color)
  $g.DrawString($text, $f, $b, (New-Object Drawing.RectangleF($x, $y, $w, $h)))
  $f.Dispose(); $b.Dispose()
}

function Draw-Arrow {
  param($g, $x1, $y1, $x2, $y2, $color, $width, $dashed)
  $pen = New-Object Drawing.Pen($color, $width)
  if ($dashed) { $pen.DashStyle = [Drawing.Drawing2D.DashStyle]::Dash }
  $pen.CustomEndCap = New-Object Drawing.Drawing2D.AdjustableArrowCap(5, 7)
  $g.DrawLine($pen, $x1, $y1, $x2, $y2)
  $pen.Dispose()
}

function Draw-Background {
  param($g, $w, $h, $title, $right, $accent)
  $b = New-Object Drawing.SolidBrush($LGRAY)
  $g.FillRectangle($b, 0, 0, $w, $h)
  $b.Dispose()
  $wb = New-Object Drawing.SolidBrush($WHITE)
  $g.FillRectangle($wb, 0, 0, $w, 80)
  $wb.Dispose()
  $gb = New-Object Drawing.SolidBrush($accent)
  $g.FillRectangle($gb, 0, 0, $w, 6)
  $gb.Dispose()
  Draw-Str $g $title 44 26 700 36 20 $true $DARK ([Drawing.StringAlignment]::Near)
  $f = New-Mono 16 $false
  $b2 = New-Object Drawing.SolidBrush($GRAY)
  $sf = New-Object Drawing.StringFormat
  $sf.Alignment = [Drawing.StringAlignment]::Far
  $g.DrawString($right, $f, $b2, (New-Object Drawing.RectangleF(0, 28, ($w - 44), 32)), $sf)
  $f.Dispose(); $b2.Dispose(); $sf.Dispose()
}

# ═══════════════════════════════════════════════════════════════
# 여기서부터 게시글별 내용. 5장을 같은 패턴으로 복사해서 쓴다.
# 구성: 01 표지 / 02 개념·원리 / 03 명령·설정 / 04 예시 도식 / 05 체크리스트
# 제목은 y=120~170, 본문 도형은 y=210 이후로 잡으면 겹치지 않는다.
# ═══════════════════════════════════════════════════════════════

# ── 01 표지 ─────────────────────────────────────────────────────
$c = New-C $W $H $LGRAY
$bmp = $c[0]; $g = $c[1]
Draw-Background $g $W $H $HeaderTitle $HeaderRight $ACCENT

Draw-Str $g "데스크톱에서" 66 156 1060 90 70 $true $DARK ([Drawing.StringAlignment]::Near)
Draw-Str $g "AI 팀을 지휘" 66 246 1060 90 70 $true $ACCENT ([Drawing.StringAlignment]::Near)
Draw-Str $g "목표를 할 일로 쪼개는 Commander" 70 366 1050 40 25 $false $GRAY ([Drawing.StringAlignment]::Near)

$chips = @("MIT", "9k stars", "macOS·Windows", "로컬 우선")
$cx = 66
foreach ($t in $chips) {
  Draw-RoundBox $g $cx 436 226 62 31 $WHITE $BORDER 2
  Draw-Str $g $t ($cx + 8) 454 210 32 21 $true $DARK ([Drawing.StringAlignment]::Center)
  $cx += 236
}

Draw-Str $g "출처: github.com/Orkas-AI/Orkas" 70 556 1040 40 24 $false ([Drawing.Color]::FromArgb(80, 86, 100)) ([Drawing.StringAlignment]::Near)

$bmp.Save("$OutDir\01-표지.png", [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()

# ── 02 카드 4개(개념/원리) ─────────────────────────────────────
$c = New-C $W $H $LGRAY
$bmp = $c[0]; $g = $c[1]
Draw-Background $g $W $H $HeaderTitle $HeaderRight $ACCENT

Draw-Str $g "팀 구성" 44 126 1080 56 44 $true $DARK ([Drawing.StringAlignment]::Near)
$cards = @(
  @("01", "커맨더", "목표 분해·배정"),
  @("02", "전문가", "16개 내장"),
  @("03", "투두", "자동 진행"),
  @("04", "커넥터", "외부 서비스")
)
foreach ($it in $cards) {
  $i = [int]$it[0] - 1
  $x = 44 + ($i * 282)
  Draw-RoundBox $g $x 236 250 300 16 $WHITE $BORDER 2
  Draw-Str $g $it[0] ($x + 22) 258 80 40 30 $true $ACCENT ([Drawing.StringAlignment]::Near)
  Draw-Str $g $it[1] ($x + 22) 310 206 40 23 $true $DARK ([Drawing.StringAlignment]::Near)
  Draw-Str $g $it[2] ($x + 22) 360 206 120 19 $false $GRAY ([Drawing.StringAlignment]::Near)
}

$bmp.Save("$OutDir\02-원리.png", [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()

# ── 03 명령·설정 ───────────────────────────────────────────────
$c = New-C $W $H $LGRAY
$bmp = $c[0]; $g = $c[1]
Draw-Background $g $W $H $HeaderTitle $HeaderRight $ACCENT

Draw-Str $g "소스 실행" 44 122 1080 56 44 $true $DARK ([Drawing.StringAlignment]::Near)
$rows = @(
  @("다운로드", "orkas.ai/download"),
  @("모델", "자체 키 또는 내장"),
  @("자동화", "예약·반복 실행"),
  @("승인", "외부 행위 전 확인")
)
$y = 206
foreach ($r in $rows) {
  Draw-RoundBox $g 44 $y 220 62 10 $WHITE $BORDER 2
  Draw-Str $g $r[0] 66 ($y + 18) 180 34 20 $true $DARK ([Drawing.StringAlignment]::Near)
  Draw-RoundBox $g 278 $y 878 62 10 ([Drawing.Color]::FromArgb(23, 26, 33)) $null 0
  Draw-MonoStr $g $r[1] 300 ($y + 18) 830 34 20 ([Drawing.Color]::FromArgb(226, 232, 240))
  $y += 78
}

$bmp.Save("$OutDir\03-명령.png", [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()

# ── 04 예시 도식 ───────────────────────────────────────────────
$c = New-C $W $H $LGRAY
$bmp = $c[0]; $g = $c[1]
Draw-Background $g $W $H $HeaderTitle $HeaderRight $ACCENT

Draw-Str $g "작업 흐름" 44 118 1080 56 44 $true $DARK ([Drawing.StringAlignment]::Near)

Draw-RoundBox $g 60 260 220 86 12 $WHITE $ACCENT 2
Draw-Str $g "목표" 80 282 180 36 22 $true $ACCENT ([Drawing.StringAlignment]::Near)
Draw-Str $g "프로젝트 생성" 80 308 180 24 16 $false $GRAY ([Drawing.StringAlignment]::Near)

Draw-RoundBox $g 480 260 240 86 12 $WHITE $GREEN 2
Draw-Str $g "분배" 500 282 200 36 22 $true $GREEN ([Drawing.StringAlignment]::Near)
Draw-Str $g "에이전트 배정" 500 308 200 24 16 $false $GRAY ([Drawing.StringAlignment]::Near)

Draw-RoundBox $g 900 260 240 86 12 $WHITE $ORANGE 2
Draw-Str $g "산출" 920 282 200 36 22 $true $ORANGE ([Drawing.StringAlignment]::Near)
Draw-Str $g "파일로 전달" 920 308 200 24 16 $false $GRAY ([Drawing.StringAlignment]::Near)

Draw-Arrow $g 280 303 480 303 $GRAY 3 $false
Draw-Arrow $g 720 303 900 303 $GRAY 3 $false

Draw-DashBox $g 480 470 400 90 12 $WHITE $GRAY 2
Draw-Str $g "PC가 꺼지면 자동화도 멈춘다" 500 498 360 40 19 $true $GRAY ([Drawing.StringAlignment]::Near)

$bmp.Save("$OutDir\04-도식.png", [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()

# ── 05 체크리스트 ───────────────────────────────────────────────
$c = New-C $W $H $LGRAY
$bmp = $c[0]; $g = $c[1]
Draw-Background $g $W $H $HeaderTitle $HeaderRight $ACCENT

Draw-Str $g "결정 전 확인" 44 122 1080 56 44 $true $DARK ([Drawing.StringAlignment]::Near)
$items = @(
  @("01", "라이선스", "MIT 오픈소스"),
  @("02", "기능", "패키지 앱 전용 多"),
  @("03", "비용", "에이전트 병렬 주의"),
  @("04", "성숙", "초기 프로젝트")
)
foreach ($it in $items) {
  $i = [int]$it[0] - 1
  $col = $i % 2
  $row = [Math]::Floor($i / 2)
  $x = 44 + ($col * 562)
  $y = 206 + ($row * 186)
  Draw-RoundBox $g $x $y 540 160 16 $WHITE $BORDER 2
  Draw-Str $g $it[0] ($x + 26) ($y + 24) 60 40 28 $true $ACCENT ([Drawing.StringAlignment]::Near)
  Draw-Str $g $it[1] ($x + 88) ($y + 26) 420 36 24 $true $DARK ([Drawing.StringAlignment]::Near)
  Draw-Str $g $it[2] ($x + 26) ($y + 82) 490 66 18 $false $GRAY ([Drawing.StringAlignment]::Near)
}

$bmp.Save("$OutDir\05-체크.png", [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()

Write-Output "DONE"
Get-ChildItem $OutDir | Select-Object Name, Length | Format-Table -AutoSize
