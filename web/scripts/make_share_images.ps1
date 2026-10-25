# Makes the link-preview pictures (1200 x 630) shown when a page of the site is shared on WhatsApp, LinkedIn,
# Facebook, iMessage, Slack, Teams or X: a navy brand background, the orange favicon mark in the middle and the
# page's title underneath. Run:  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\make_share_images.ps1
# Needs Windows (it uses the built-in System.Drawing). The pictures are saved in assets\ and committed.
Add-Type -AssemblyName System.Drawing
$root = Split-Path -Parent $PSScriptRoot
$assets = Join-Path $root "assets"

# file name -> title shown under the mark
$pages = [ordered]@{
  "og-image.jpg"    = "Nationwide staffing, based in Erie, PA"                  # home (the original file name stays valid)
  "og-services.jpg" = "Staffing services across the USA"
  "og-about.jpg"    = "Connecting clients, vendors, and candidates"
  "og-jobs.jpg"     = "Open roles across the USA"
  "og-contact.jpg"  = "Get in touch with our team"
  "og-insights.jpg" = "Insights on hiring and the job market"
}

$fonts = New-Object System.Drawing.Text.PrivateFontCollection
$fonts.AddFontFile((Join-Path $assets "fonts\nasalization.otf"))
$family = $fonts.Families[0]
$mark = [System.Drawing.Image]::FromFile((Join-Path $assets "favicon-512.png"))   # the orange mark on a transparent square
$fmt = [System.Drawing.StringFormat]::GenericTypographic
$SPACING = 4

# a space is as wide as a letter, so the words stay clearly apart
function Glyph-Width($g, $font, $ch) {
  if ($ch -eq ' ') { return $font.Size * 0.62 }
  return $g.MeasureString([string]$ch, $font, 400, $fmt).Width
}

function Measure-Line($g, $font, $text) {
  $sum = 0.0
  foreach ($ch in $text.ToCharArray()) { $sum += (Glyph-Width $g $font $ch) + $SPACING }
  return $sum - $SPACING
}

function New-ShareImage($title, $path) {
  $W = 1200; $H = 630
  $bmp = New-Object System.Drawing.Bitmap($W, $H, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.SmoothingMode = 'HighQuality'; $g.InterpolationMode = 'HighQualityBicubic'; $g.PixelOffsetMode = 'HighQuality'
  $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit

  # brand navy, brighter at the top left and deeper at the bottom right
  $bg = New-Object System.Drawing.Drawing2D.LinearGradientBrush((New-Object System.Drawing.Rectangle(0, 0, $W, $H)),
    [System.Drawing.Color]::FromArgb(255, 36, 70, 160), [System.Drawing.Color]::FromArgb(255, 10, 20, 64), 35)
  $g.FillRectangle($bg, 0, 0, $W, $H)

  # a faint, very large copy of the mark as texture, cropped by the right edge
  $ia = New-Object System.Drawing.Imaging.ImageAttributes
  $cm = New-Object System.Drawing.Imaging.ColorMatrix
  $cm.Matrix00 = 0; $cm.Matrix11 = 0; $cm.Matrix22 = 0              # a white copy of the mark, not an orange one
  $cm.Matrix40 = 1; $cm.Matrix41 = 1; $cm.Matrix42 = 1
  $cm.Matrix33 = 0.06
  $ia.SetColorMatrix($cm)
  $g.DrawImage($mark, (New-Object System.Drawing.Rectangle(640, -40, 760, 760)), 0, 0, $mark.Width, $mark.Height, [System.Drawing.GraphicsUnit]::Pixel, $ia)

  # a soft glow behind the mark
  $glowPath = New-Object System.Drawing.Drawing2D.GraphicsPath
  $glowPath.AddEllipse(300, 40, 600, 420)
  $glow = New-Object System.Drawing.Drawing2D.PathGradientBrush($glowPath)
  $glow.CenterColor = [System.Drawing.Color]::FromArgb(70, 120, 160, 255)
  $glow.SurroundColors = @([System.Drawing.Color]::FromArgb(0, 120, 160, 255))
  $g.FillPath($glow, $glowPath)

  # the title: capitals, wide spacing, in one line when it fits, otherwise two balanced lines
  $font = New-Object System.Drawing.Font($family, 32, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
  $text = $title.ToUpper()
  $limit = 1040
  $lines = @($text)
  if ((Measure-Line $g $font $text) -gt $limit) {
    $words = $text.Split(' ')
    $best = $null; $bestWidth = 1e9
    for ($k = 1; $k -lt $words.Count; $k++) {
      $a = ($words[0..($k - 1)] -join ' '); $b = ($words[$k..($words.Count - 1)] -join ' ')
      $m = [Math]::Max((Measure-Line $g $font $a), (Measure-Line $g $font $b))
      if ($m -lt $bestWidth) { $bestWidth = $m; $best = @($a, $b) }
    }
    $lines = $best
  }

  # the group (mark + gap + title) is centred vertically
  $markSize = 250; $gap = 42; $lineHeight = 48
  $group = $markSize + $gap + $lines.Count * $lineHeight
  $top = ($H - $group) / 2
  $g.DrawImage($mark, (($W - $markSize) / 2), $top, $markSize, $markSize)

  $brush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 214, 236, 255))
  $y = $top + $markSize + $gap
  foreach ($line in $lines) {
    $x = ($W - (Measure-Line $g $font $line)) / 2
    foreach ($ch in $line.ToCharArray()) {
      $g.DrawString([string]$ch, $font, $brush, $x, $y, $fmt)
      $x += (Glyph-Width $g $font $ch) + $SPACING
    }
    $y += $lineHeight
  }
  $g.Dispose()

  $codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
  $params = New-Object System.Drawing.Imaging.EncoderParameters(1)
  $params.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, [long]90)
  $bmp.Save($path, $codec, $params)
  $bmp.Dispose()
}

foreach ($name in $pages.Keys) {
  $out = Join-Path $assets $name
  New-ShareImage $pages[$name] $out
  "{0,-18} {1,4} KB   {2}" -f $name, [int]((Get-Item $out).Length / 1024), $pages[$name]
}
