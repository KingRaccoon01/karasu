# Karasu 🐦‍⬛

Takip ettiğin manga ve animelere yeni bölüm geldiğinde Windows bildirimi gönderen küçük bir haberci.
Bildirime tıklayınca bölümün sayfası açılır.

- **Manga:** [MangaDex](https://mangadex.org) — İngilizce/Türkçe çeviriler
- **Anime:** [AniList](https://anilist.co) — yayındaki son sezonu otomatik bulur (yeni sezon başlayınca kendiliğinden geçer)

İkisi de API anahtarı gerektirmez.

## Kurulum

Windows 10/11 ve Python 3.10+ gerekir.

```
pip install -r requirements.txt
```

## Takip listesi

İlk çalıştırmada örnek bir `takip.txt` oluşur. Her satıra bir seri yaz:

```
manga: One Piece
anime: Sousou no Frieren
# ile başlayan satırlar yorumdur
```

Resmi adı kullan; kısmi adda yan eser (doujinshi, renkli sürüm) seçilebilir.

## Çalıştırma

```
python bildirici.py          # bir kez kontrol eder
python bildirici.py --test   # ağsız self-test
```

İlk çalıştırmada mevcut bölümler kaydedilir; bildirim sadece sonra gelen yeni bölümlerde gelir.

## Otomatik çalıştırma

`kur.bat` dosyasına çift tıkla. Karasu her gün 20:00'de kontrol eder; bilgisayar o saatte kapalıysa açılınca çalışır.
Bildirimler Windows oturumu açıkken görünür.

`kur.bat`, Python'u `%LOCALAPPDATA%\Programs\Python\Python311` altında arar. Python'un başka bir yerdeyse dosyadaki yolu değiştir.

Kaldırmak için:

```
schtasks /delete /tn "MangaAnimeBildirici" /f
```

## Notlar

- Lisans nedeniyle MangaDex'ten kaldırılmış serilerde sonuç düşük ya da boş çıkabilir.
- Hatalar `hata.log` dosyasına yazılır.

## Lisans

MIT
