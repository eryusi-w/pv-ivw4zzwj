param([string]$OutDir = "")

Add-Type -AssemblyName System.Drawing

if (-not $OutDir) { $OutDir = Join-Path $PSScriptRoot "images" }
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }

$INDIGO = [Drawing.Color]::FromArgb(79, 70, 229)
$DARK   = [Drawing.Color]::FromArgb(23, 26, 33)
$GRAY   = [Drawing.Color]::FromArgb(105, 112, 124)
$LGRAY  = [Drawing.Color]::FromArgb(245, 247, 250)
$BORDER = [Drawing.Color]::FromArgb(220, 224, 231)
$GREEN  = [Drawing.Color]::FromArgb(15, 157, 110)
$ORANGE = [Drawing.Color]::FromArgb(224, 122, 47)
$RED    = [Drawing.Color]::FromArgb(198, 68, 68)
$PURPLE = [Drawing.Color]::FromArgb(124, 58, 237)
$WHITE  = [Drawing.Color]::White

$W = 1200; $H = 675
$HeaderTitle = "STRUCTURIZR 가이드"
$HeaderRight = "structurizr/structurizr"

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
  param($g, $x1, $y1, $x2, $y2, $color, $width)
  $pen = New-Object Drawing.Pen($color, $width)
  $pen.CustomEndCap = New-Object Drawing.Drawing2D.AdjustableArrowCap(5, 7)
  $g.DrawLine($pen, $x1, $y1, $x2, $y2)
  $pen.Dispose()
}

function Draw-Background {
  param($g, $w, $h)
  $b = New-Object Drawing.SolidBrush($LGRAY)
  $g.FillRectangle($b, 0, 0, $w, $h)
  $b.Dispose()
  $wb = New-Object Drawing.SolidBrush($WHITE)
  $g.FillRectangle($wb, 0, 0, $w, 92)
  $wb.Dispose()
  $gb = New-Object Drawing.SolidBrush($INDIGO)
  $g.FillRectangle($gb, 0, 0, $w, 7)
  $gb.Dispose()
  Draw-Str $g $HeaderTitle 44 32 700 40 21 $true $DARK ([Drawing.StringAlignment]::Near)
  $f = New-Mono 18 $false
  $b2 = New-Object Drawing.SolidBrush($GRAY)
  $sf = New-Object Drawing.StringFormat
  $sf.Alignment = [Drawing.StringAlignment]::Far
  $g.DrawString($HeaderRight, $f, $b2, (New-Object Drawing.RectangleF(0, 34, ($w - 44), 36)), $sf)
  $f.Dispose(); $b2.Dispose(); $sf.Dispose()
}

# ── 01 표지 ────────────────────────────────────────────────────
$c = New-C $W $H $LGRAY
$bmp = $c[0]; $g = $c[1]
Draw-Background $g $W $H

Draw-Str $g "확정된 구조를" 66 148 1060 84 68 $true $DARK ([Drawing.StringAlignment]::Near)
Draw-Str $g "보관하는 모델" 66 236 1060 84 68 $true $INDIGO ([Drawing.StringAlignment]::Near)
Draw-Str $g "Structurizr로 아키텍처를 코드처럼 관리하는 방법" 70 356 1060 40 25 $false $GRAY ([Drawing.StringAlignment]::Near)

$chips = @("단일 모델", "다중 뷰", "Git 보관", "C4 호환")
$cx = 66
foreach ($t in $chips) {
  Draw-RoundBox $g $cx 432 232 62 31 $WHITE $BORDER 2
  Draw-Str $g $t ($cx + 8) 450 216 32 21 $true $DARK ([Drawing.StringAlignment]::Center)
  $cx += 242
}

Draw-Str $g "models as code · C4 model 레퍼런스 구현" 70 556 1040 40 23 $false ([Drawing.Color]::FromArgb(80, 86, 100)) ([Drawing.StringAlignment]::Near)

$bmp.Save("$OutDir\01-표지.png", [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()

# ── 02 모델 → 뷰 ───────────────────────────────────────────────
$c = New-C $W $H $LGRAY
$bmp = $c[0]; $g = $c[1]
Draw-Background $g $W $H

Draw-Str $g "모델 하나, 뷰 여러 개" 44 126 1080 56 44 $true $DARK ([Drawing.StringAlignment]::Near)

Draw-RoundBox $g 60 220 300 300 16 $WHITE $INDIGO 3
Draw-Str $g "MODEL" 84 244 240 30 22 $true $INDIGO ([Drawing.StringAlignment]::Near)
Draw-Str $g "workspace.dsl" 84 280 240 24 16 $false $GRAY ([Drawing.StringAlignment]::Near)
Draw-Str $g "person" 84 322 240 26 17 $false $DARK ([Drawing.StringAlignment]::Near)
Draw-Str $g "softwareSystem" 84 352 240 26 17 $false $DARK ([Drawing.StringAlignment]::Near)
Draw-Str $g "container" 84 382 240 26 17 $false $DARK ([Drawing.StringAlignment]::Near)
Draw-Str $g "component" 84 412 240 26 17 $false $DARK ([Drawing.StringAlignment]::Near)
Draw-Str $g "relationship" 84 442 240 26 17 $false $DARK ([Drawing.StringAlignment]::Near)
Draw-Str $g "요소 + 관계" 84 486 240 24 15 $false $GRAY ([Drawing.StringAlignment]::Near)

$views = @(
  @("시스템 컨텍스트", "누구와 연결되나", $INDIGO),
  @("컨테이너", "배포 단위와 통신", $PURPLE),
  @("컴포넌트", "내부 책임 분리", $ORANGE),
  @("동적 · 배포", "흐름과 배치", $GREEN)
)
$vy = 206
foreach ($v in $views) {
  Draw-RoundBox $g 470 $vy 320 74 12 $WHITE $BORDER 2
  Draw-Str $g $v[0] 492 ($vy + 11) 280 28 21 $true $v[2] ([Drawing.StringAlignment]::Near)
  Draw-Str $g $v[1] 492 ($vy + 41) 280 24 15 $false $GRAY ([Drawing.StringAlignment]::Near)
  Draw-Arrow $g 366 ($vy + 37) 462 ($vy + 37) $GRAY 3
  $vy += 84
}

Draw-RoundBox $g 60 548 1112 74 14 ([Drawing.Color]::FromArgb(238, 238, 253)) $null 0
Draw-Str $g "뷰는 모델에서 파생된다. 그림을 고치지 않고 모델을 고친다" 84 570 1064 44 22 $true ([Drawing.Color]::FromArgb(49, 46, 129)) ([Drawing.StringAlignment]::Near)

$bmp.Save("$OutDir\02-원리.png", [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()

# ── 03 DSL ─────────────────────────────────────────────────────
$c = New-C $W $H $LGRAY
$bmp = $c[0]; $g = $c[1]
Draw-Background $g $W $H

Draw-Str $g "DSL 기본 구조" 44 122 1080 56 44 $true $DARK ([Drawing.StringAlignment]::Near)

Draw-RoundBox $g 44 196 780 424 14 $DARK $null 0

$lines = @(
  'workspace {',
  '  model {',
  '    u  = person "User"',
  '    ss = softwareSystem "System"',
  '    u -> ss "Uses"',
  '  }',
  '  views {',
  '    systemContext ss {',
  '      include *',
  '    }',
  '  }',
  '}'
)
$ly = 222
foreach ($ln in $lines) {
  Draw-MonoStr $g $ln 72 $ly 730 30 19 ([Drawing.Color]::FromArgb(226, 232, 240))
  $ly += 32
}

$notes = @(
  @("파일 하나", "workspace.dsl"),
  @("모델 + 뷰", "한 파일에 함께"),
  @("Git diff", "변경이 텍스트로")
)
$ny = 208
foreach ($n in $notes) {
  Draw-RoundBox $g 852 $ny 304 120 14 $WHITE $BORDER 2
  Draw-Str $g $n[0] 876 ($ny + 22) 256 34 22 $true $INDIGO ([Drawing.StringAlignment]::Near)
  Draw-Str $g $n[1] 876 ($ny + 62) 256 40 16 $false $GRAY ([Drawing.StringAlignment]::Near)
  $ny += 136
}

$bmp.Save("$OutDir\03-명령.png", [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()

# ── 04 확인 · 내보내기 ─────────────────────────────────────────
$c = New-C $W $H $LGRAY
$bmp = $c[0]; $g = $c[1]
Draw-Background $g $W $H

Draw-Str $g "확인하고 내보내는 방법" 44 122 1080 56 44 $true $DARK ([Drawing.StringAlignment]::Near)

$rows = @(
  @("플레이그라운드", "playground.structurizr.com"),
  @("로컬 실행", "docker run ... structurizr/structurizr local"),
  @("검사", "structurizr-cli validate -workspace workspace.dsl"),
  @("내보내기", "structurizr-cli export -format mermaid")
)
$ry = 208
foreach ($r in $rows) {
  Draw-RoundBox $g 44 $ry 230 60 10 $WHITE $BORDER 2
  Draw-Str $g $r[0] 66 ($ry + 17) 190 32 19 $true $DARK ([Drawing.StringAlignment]::Near)
  Draw-RoundBox $g 288 $ry 868 60 10 $DARK $null 0
  Draw-MonoStr $g $r[1] 310 ($ry + 18) 830 30 18 ([Drawing.Color]::FromArgb(226, 232, 240))
  $ry += 78
}

Draw-RoundBox $g 44 540 1112 62 12 ([Drawing.Color]::FromArgb(236, 253, 245)) $null 0
Draw-Str $g "PNG · SVG · PlantUML · Mermaid · 정적 사이트로 내보낼 수 있다" 68 557 1064 34 20 $true ([Drawing.Color]::FromArgb(6, 95, 70)) ([Drawing.StringAlignment]::Near)

$bmp.Save("$OutDir\04-도식.png", [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()

# ── 05 체크리스트 ──────────────────────────────────────────────
$c = New-C $W $H $LGRAY
$bmp = $c[0]; $g = $c[1]
Draw-Background $g $W $H

Draw-Str $g "모델을 믿기 전에 확인할 것" 44 122 1080 56 44 $true $DARK ([Drawing.StringAlignment]::Near)

$items = @(
  @("01", "코드와 동기화", "배포 단위와 요소가 1:1로 대응하는가"),
  @("02", "관계의 방향", "호출 방향과 데이터 흐름이 섞이지 않았는가"),
  @("03", "변경 이력", "요소 추가·삭제가 diff로 보이는가"),
  @("04", "자동 검사", "validate와 export가 CI에 있는가")
)
foreach ($it in $items) {
  $i = [int]$it[0] - 1
  $col = $i % 2
  $row = [Math]::Floor($i / 2)
  $x = 44 + ($col * 562)
  $y = 206 + ($row * 186)
  Draw-RoundBox $g $x $y 540 160 16 $WHITE $BORDER 2
  Draw-Str $g $it[0] ($x + 26) ($y + 24) 60 40 28 $true $INDIGO ([Drawing.StringAlignment]::Near)
  Draw-Str $g $it[1] ($x + 88) ($y + 26) 420 36 24 $true $DARK ([Drawing.StringAlignment]::Near)
  Draw-Str $g $it[2] ($x + 26) ($y + 82) 490 66 18 $false $GRAY ([Drawing.StringAlignment]::Near)
}

Draw-Str $g "모델은 정답이 아니라 합의의 기록입니다" 46 592 1080 40 21 $true ([Drawing.Color]::FromArgb(49, 46, 129)) ([Drawing.StringAlignment]::Near)

$bmp.Save("$OutDir\05-체크.png", [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()

Write-Output "DONE"
Get-ChildItem $OutDir | Select-Object Name, Length | Format-Table -AutoSize
