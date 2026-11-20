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
$HeaderTitle = "GSD Core 가이드"
$HeaderRight = "open-gsd/gsd-core"

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

Draw-Str $g "GSD Core" 66 156 1060 90 70 $true $DARK ([Drawing.StringAlignment]::Near)
Draw-Str $g "Git. Ship. Done." 66 246 1060 90 70 $true $ACCENT ([Drawing.StringAlignment]::Near)
Draw-Str $g "대규모 AI 코딩을 위한 컨텍스트 엔지니어링 프레임워크" 70 366 1050 40 25 $false $GRAY ([Drawing.StringAlignment]::Near)

$chips = @("컨텍스트 부패 방지", "스펙 기반 개발", "페이즈 루프", "에이전트 오케스트레이션")
$cx = 66
foreach ($t in $chips) {
  Draw-RoundBox $g $cx 436 226 62 31 $WHITE $BORDER 2
  Draw-Str $g $t ($cx + 8) 454 210 32 21 $true $DARK ([Drawing.StringAlignment]::Center)
  $cx += 236
}

Draw-Str $g "GitHub: open-gsd/gsd-core · MIT License · v1.7.0" 70 556 1040 40 24 $false ([Drawing.Color]::FromArgb(80, 86, 100)) ([Drawing.StringAlignment]::Near)

$bmp.Save("$OutDir\01-표지.png", [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()

# ── 02 카드 4개(개념/원리) ─────────────────────────────────────
$c = New-C $W $H $LGRAY
$bmp = $c[0]; $g = $c[1]
Draw-Background $g $W $H $HeaderTitle $HeaderRight $ACCENT

Draw-Str $g "5단계 개발 루프" 44 126 1080 56 44 $true $DARK ([Drawing.StringAlignment]::Near)
$cards = @(
  @("01", "Discuss/Plan", "구현 결정 사항을 정의하고 세부 실행 계획을 수립합니다."),
  @("02", "Execute", "깨끗한 컨텍스트의 서브에이전트가 병렬로 코드를 작성합니다."),
  @("03", "Verify", "빌드 및 테스트를 통해 결과물의 작동 여부를 엄격히 검증합니다."),
  @("04", "Ship", "최종 결과물을 배포하고 해당 단계의 기록을 아카이브합니다.")
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

Draw-Str $g "주요 명령어" 44 122 1080 56 44 $true $DARK ([Drawing.StringAlignment]::Near)
$rows = @(
  @("설치", "npx @opengsd/gsd-core@latest"),
  @("새 프로젝트", "/gsd-new-project"),
  @("온보딩", "/gsd-onboard"),
  @("상태 확인", "cat STATE.md")
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

Draw-Str $g "컨텍스트 부패 방지 구조" 44 118 1080 56 44 $true $DARK ([Drawing.StringAlignment]::Near)

Draw-RoundBox $g 60 260 220 86 12 $WHITE $ACCENT 2
Draw-Str $g "메인 세션" 80 282 180 36 22 $true $ACCENT ([Drawing.StringAlignment]::Near)
Draw-Str $g "작업 통제 및 기록" 80 308 180 24 16 $false $GRAY ([Drawing.StringAlignment]::Near)

Draw-RoundBox $g 480 260 240 86 12 $WHITE $GREEN 2
Draw-Str $g "서브 에이전트" 500 282 200 36 22 $true $GREEN ([Drawing.StringAlignment]::Near)
Draw-Str $g "신선한 컨텍스트(200k)" 500 308 200 24 16 $false $GRAY ([Drawing.StringAlignment]::Near)

Draw-RoundBox $g 900 260 240 86 12 $WHITE $ORANGE 2
Draw-Str $g "구조화 문서" 920 282 200 36 22 $true $ORANGE ([Drawing.StringAlignment]::Near)
Draw-Str $g "STATE.md / CONTEXT.md" 920 308 200 24 16 $false $GRAY ([Drawing.StringAlignment]::Near)

Draw-Arrow $g 280 303 480 303 $GRAY 3 $false
Draw-Arrow $g 720 303 900 303 $GRAY 3 $false

Draw-DashBox $g 480 470 400 90 12 $WHITE $GRAY 2
Draw-Str $g "대규모 프로젝트 안정적 확장" 500 498 360 40 19 $true $GRAY ([Drawing.StringAlignment]::Near)

$bmp.Save("$OutDir\04-도식.png", [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()

# ── 05 체크리스트 ─────────────────────────────────────────────
$c = New-C $W $H $LGRAY
$bmp = $c[0]; $g = $c[1]
Draw-Background $g $W $H $HeaderTitle $HeaderRight $ACCENT

Draw-Str $g "GSD 루프 점검 항목" 44 122 1080 56 44 $true $DARK ([Drawing.StringAlignment]::Near)
$items = @(
  @("01", "STATE.md 업데이트", "현재 작업 단계와 진행 상황이 정확히 기록되었는가?"),
  @("02", "서브에이전트 분리", "무거운 작업이 메인 세션을 오염시키지 않도록 분리했는가?"),
  @("03", "Verify 단계 통과", "테스트나 빌드 결과가 명확한 증거로 제시되었는가?"),
  @("04", "페이즈 아카이브", "완료된 단계의 문서가 향후 참조 가능하게 보관되었는가?")
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
