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

# ── 테마 (게시글마다 여기만 바꾼다) ─────────────────────────────
$ACCENT = [Drawing.Color]::FromArgb(203, 56, 55)
$DARK   = [Drawing.Color]::FromArgb(23, 26, 33)
$GRAY   = [Drawing.Color]::FromArgb(105, 112, 124)
$LGRAY  = [Drawing.Color]::FromArgb(245, 247, 250)
$BORDER = [Drawing.Color]::FromArgb(220, 224, 231)
$GREEN  = [Drawing.Color]::FromArgb(15, 157, 110)
$ORANGE = [Drawing.Color]::FromArgb(224, 122, 47)
$RED    = [Drawing.Color]::FromArgb(198, 68, 68)
$WHITE  = [Drawing.Color]::White

$W = 1200; $H = 675
$HeaderTitle = "RTK 가이드"
$HeaderRight = "rtk-ai/rtk"

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
  $g.FillRectangle($wb, 0, 0, $w, 92)
  $wb.Dispose()
  $gb = New-Object Drawing.SolidBrush($accent)
  $g.FillRectangle($gb, 0, 0, $w, 7)
  $gb.Dispose()
  Draw-Str $g $title 44 30 700 40 21 $true $DARK ([Drawing.StringAlignment]::Near)
  $f = New-Mono 18 $false
  $b2 = New-Object Drawing.SolidBrush($GRAY)
  $sf = New-Object Drawing.StringFormat
  $sf.Alignment = [Drawing.StringAlignment]::Far
  $g.DrawString($right, $f, $b2, (New-Object Drawing.RectangleF(0, 32, ($w - 44), 36)), $sf)
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

Draw-Str $g "RTK" 66 156 1060 90 70 $true $DARK ([Drawing.StringAlignment]::Near)
Draw-Str $g "Rust Token Killer" 66 246 1060 90 70 $true $ACCENT ([Drawing.StringAlignment]::Near)
Draw-Str $g "AI 에이전트를 위한 명령어 출력 압축기" 70 366 1050 40 25 $false $GRAY ([Drawing.StringAlignment]::Near)

$chips = @("100+ 지원 명령어", "평균 60% 토큰 절감", "prompt cache hit 증가", "에이전트 연동 용이")
$cx = 66
foreach ($t in $chips) {
  Draw-RoundBox $g $cx 436 226 62 31 $WHITE $BORDER 2
  Draw-Str $g $t ($cx + 8) 454 210 32 21 $true $DARK ([Drawing.StringAlignment]::Center)
  $cx += 236
}

Draw-Str $g "GitHub: rtk-ai/rtk · Apache-2.0 + BUSL-1.1" 70 556 1040 40 24 $false ([Drawing.Color]::FromArgb(80, 86, 100)) ([Drawing.StringAlignment]::Near)

$bmp.Save("$OutDir\01-표지.png", [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()

# ── 02 카드 4개(개념/원리) ─────────────────────────────────────
$c = New-C $W $H $LGRAY
$bmp = $c[0]; $g = $c[1]
Draw-Background $g $W $H $HeaderTitle $HeaderRight $ACCENT

Draw-Str $g "핵심 필터링 전략" 44 126 1080 56 44 $true $DARK ([Drawing.StringAlignment]::Near)
$cards = @(
  @("01", "스마트 필터링", "주석, 여백, boilerplate 제거"),
  @("02", "그룹화", "유사한 항목 통합 (같은 디렉토리 파일 묶기, 유사한 에러군 그룹화)"),
  @("03", "축소", "관련성 높은 컨텍스트만 유지, redundant 내용 잘라내기"),
  @("04", "중복 제거", "반복된 로그 라인 카운트 표시")
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

Draw-Str $g "주요 명령어 및 통계" 44 122 1080 56 44 $true $DARK ([Drawing.StringAlignment]::Near)
$rows = @(
  @("설치", "rtk init -g"),
  @("절감 효과", "rtk gain"),
  @("기회 탐색", "rtk discover"),
  @("세션 통계", "rtk session"),
  @("바이패스", "rtk bypass <cmd>")
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

Draw-Str $g "RTK 적용 전후 비교" 44 118 1080 56 44 $true $DARK ([Drawing.StringAlignment]::Near)

Draw-RoundBox $g 60 260 220 86 12 $WHITE $ACCENT 2
Draw-Str $g "일반 출력" 80 282 180 36 22 $true $ACCENT ([Drawing.StringAlignment]::Near)
Draw-Str $g "전체 로그와 디테일 표시" 80 308 180 24 16 $false $GRAY ([Drawing.StringAlignment]::Near)

Draw-RoundBox $g 480 260 240 86 12 $WHITE $GREEN 2
Draw-Str $g "RTK 압축 전" 500 282 200 36 22 $true $GREEN ([Drawing.StringAlignment]::Near)
Draw-Str $g "장황한 pytest output" 500 308 200 24 16 $false $GRAY ([Drawing.StringAlignment]::Near)

Draw-RoundBox $g 900 260 240 86 12 $WHITE $ORANGE 2
Draw-Str $g "RTK 압축 후" 920 282 200 36 22 $true $ORANGE ([Drawing.StringAlignment]::Near)
Draw-Str $g "핵심 실패 메시지만 표시" 920 308 200 24 16 $false $GRAY ([Drawing.StringAlignment]::Near)

Draw-Arrow $g 280 303 480 303 $GRAY 3 $false
Draw-Arrow $g 720 303 900 303 $GRAY 3 $false

Draw-DashBox $g 480 470 400 90 12 $WHITE $GRAY 2
Draw-Str $g "컨텍스트 폭증으로부터 해방" 500 498 360 40 19 $true $GRAY ([Drawing.StringAlignment]::Near)

$bmp.Save("$OutDir\04-도식.png", [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()

# ── 05 체크리스트 ─────────────────────────────────────────────
$c = New-C $W $H $LGRAY
$bmp = $c[0]; $g = $c[1]
Draw-Background $g $W $H $HeaderTitle $HeaderRight $ACCENT

Draw-Str $g "RTK 적용 점검 항목" 44 122 1080 56 44 $true $DARK ([Drawing.StringAlignment]::Near)
$items = @(
  @("01", "토큰 절감 확인", "세션당 토큰 사용량이 감소했는지 확인"),
  @("02", "캐시 히트율 상승", "프롬프트 캐시 적중률이 개선되었는지 체크"),
  @("03", "핵심 정보 유지", "압축된 출력에도 필수 정보가 빠짐없이 포함되는지 검증"),
  @("04", "작업 효율성", "문제 해결에 걸리는 시간이 단축되었는지 확인")
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
