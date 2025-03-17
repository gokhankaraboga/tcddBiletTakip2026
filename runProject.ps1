Write-Host "TCDD Bilet Takip programi baslatiliyor..."
Write-Host "Programi durdurmak icin Ctrl+C."
Write-Host ""

# Gerekli Python paketlerini yükle
Write-Host "Gerekli paketler kontrol ediliyor ve yukleniyor..."
pip install selenium webdriver-manager requests

Write-Host "Paket kurulumu tamamlandi."
Write-Host "------------------------"

while ($true) {
    # Çalıştırma zamanını göster
    $currentTime = Get-Date -Format "dd.MM.yyyy HH:mm:ss"
    Write-Host "[$currentTime] Program calistiriliyor..."
    
    # Python scriptini çalıştır
    python main.py
    
    Write-Host "1 dakika bekleniyor..."
    Write-Host "------------------------"
    
    # 60 saniye bekle
    Start-Sleep -Seconds 60
}
