# URLs das dependências
$deps = @{
    "jquery/jquery.min.js" = "https://code.jquery.com/jquery-3.6.0.min.js"
    "jquery-ui/jquery-ui.min.js" = "https://code.jquery.com/ui/1.13.2/jquery-ui.min.js"
    "jquery-ui/jquery-ui.min.css" = "https://code.jquery.com/ui/1.13.2/themes/base/jquery-ui.min.css"
    "bootstrap-datepicker/bootstrap-datepicker.min.js" = "https://cdnjs.cloudflare.com/ajax/libs/bootstrap-datepicker/1.9.0/js/bootstrap-datepicker.min.js"
    "bootstrap-datepicker/bootstrap-datepicker.min.css" = "https://cdnjs.cloudflare.com/ajax/libs/bootstrap-datepicker/1.9.0/css/bootstrap-datepicker.min.css"
    "bootstrap-datepicker/locales/bootstrap-datepicker.pt-BR.min.js" = "https://cdnjs.cloudflare.com/ajax/libs/bootstrap-datepicker/1.9.0/locales/bootstrap-datepicker.pt-BR.min.js"
}

# Download cada arquivo
foreach ($path in $deps.Keys) {
    $url = $deps[$path]
    $outFile = $path
    Write-Host "Downloading $url to $outFile"
    Invoke-WebRequest -Uri $url -OutFile $outFile
}
