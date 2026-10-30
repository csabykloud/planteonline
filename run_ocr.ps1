Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]

# Helper to await WinRT async operations
$asTaskGeneric = [System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.IsGenericMethod } | Select-Object -First 1

function AwaitTask($asyncOp, $type) {
    $m = $asTaskGeneric.MakeGenericMethod($type)
    $task = $m.Invoke($null, @($asyncOp))
    $task.Wait()
    return $task.Result
}

$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if (-not $engine) {
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new("en-US"))
}

$pages = Get-ChildItem "import_produse\pdf_pages\page_*.jpg" | Sort-Object Name
$allText = ""

foreach ($p in $pages) {
    Write-Host "Processing OCR on $($p.Name)..."
    $fileOp = [Windows.Storage.StorageFile]::GetFileFromPathAsync($p.FullName)
    $file = AwaitTask $fileOp ([Windows.Storage.StorageFile])

    $streamOp = $file.OpenAsync([Windows.Storage.FileAccessMode]::Read)
    $stream = AwaitTask $streamOp ([Windows.Storage.Streams.IRandomAccessStream])

    $decoderOp = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)
    $decoder = AwaitTask $decoderOp ([Windows.Graphics.Imaging.BitmapDecoder])

    $bmpOp = $decoder.GetSoftwareBitmapAsync()
    $bmp = AwaitTask $bmpOp ([Windows.Graphics.Imaging.SoftwareBitmap])

    $ocrOp = $engine.RecognizeAsync($bmp)
    $ocrResult = AwaitTask $ocrOp ([Windows.Media.Ocr.OcrResult])

    $pageHeader = "`n=== $($p.Name) ===`n"
    $pageText = $ocrResult.Text
    $allText += $pageHeader + $pageText
    Write-Host "  Found $( $pageText.Length ) characters"
}

[System.IO.File]::WriteAllText("import_produse\pdf_extracted_text.txt", $allText, [System.Text.Encoding]::UTF8)
Write-Host "Done! Saved to import_produse\pdf_extracted_text.txt"
