"""Takip edilen manga/animelerde yeni bölüm çıkınca Windows 11 bildirimi gösterir."""
import sqlite3
import sys
import tempfile
import traceback
from datetime import datetime
from pathlib import Path

import kaynaklar

KLASOR = Path(__file__).parent  # Görev Zamanlayıcı cwd'yi System32 yapar, yollar buna göre
TAKIP, DB, LOG = KLASOR / "takip.txt", KLASOR / "durum.db", KLASOR / "hata.log"
ORNEK = "# Her satıra bir seri: manga: Ad  veya  anime: Ad\nmanga: One Piece\nanime: Frieren\n"
KAYNAK = {"manga": kaynaklar.son_manga_bolumu, "anime": kaynaklar.son_anime_bolumu}


def logla(hata):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {hata}\n")


def ayristir(metin):
    """takip.txt metnini [(tur, ad), ...] yapar; yorum, boş ve hatalı satırlar atlanır."""
    sonuc = []
    for satir in metin.splitlines():
        satir = satir.strip()
        tur, ayrac, ad = satir.partition(":")
        tur, ad = tur.strip().lower(), ad.strip()
        if satir.startswith("#") or not ayrac or tur not in KAYNAK or not ad:
            continue
        sonuc.append((tur, ad))
    return sonuc


def karar(db, tur, ad, bolum):
    """True ise bildirim gösterilmeli. Kaydı günceller; yalnızca "bolum" karşılaştırılır."""
    satir = db.execute("SELECT bolum FROM durum WHERE tur=? AND ad=?", (tur, ad)).fetchone()
    db.execute("INSERT OR REPLACE INTO durum VALUES (?,?,?)", (tur, ad, bolum))
    db.commit()
    return satir is not None and satir[0] != bolum


def db_ac(yol):
    db = sqlite3.connect(yol)
    db.execute("CREATE TABLE IF NOT EXISTS durum (tur TEXT, ad TEXT, bolum TEXT, PRIMARY KEY (tur, ad))")
    return db


def bildir(sonuc):
    import win11toast  # yalnızca burada gerekli; --test ağsız/bildirimsiz çalışsın
    win11toast.notify(f"{sonuc['baslik']} — Bölüm {sonuc['bolum']}", on_click=sonuc["url"])


def calistir():
    if not TAKIP.exists():
        TAKIP.write_text(ORNEK, encoding="utf-8")
    db = db_ac(DB)
    for tur, ad in ayristir(TAKIP.read_text(encoding="utf-8")):
        try:
            sonuc = KAYNAK[tur](ad)
            if sonuc is None or not karar(db, tur, ad, sonuc["bolum"]):
                continue
            try:
                bildir(sonuc)
            except Exception:
                logla(f"[{tur}: {ad}] bildirim gösterilemedi\n{traceback.format_exc()}")
        except Exception:
            logla(f"[{tur}: {ad}]\n{traceback.format_exc()}")


def test():
    assert ayristir("# yorum\n\nmanga: One Piece\n anime : Frieren \nkitap: X\nmanga:\nsaçma\nmanga: A: B") == [
        ("manga", "One Piece"), ("anime", "Frieren"), ("manga", "A: B")]
    assert ayristir("") == []
    with tempfile.TemporaryDirectory() as d:
        db = db_ac(Path(d) / "t.db")
        assert karar(db, "manga", "X", "1") is False  # ilk kayıt: bildirim yok
        assert karar(db, "manga", "X", "1") is False  # aynı bölüm
        assert karar(db, "manga", "X", "2") is True   # yeni bölüm
        assert karar(db, "manga", "X", "2") is False  # güncellendi
        assert karar(db, "anime", "X", "1") is False  # tür ayrı anahtar
        db.close()
    print("OK")


if __name__ == "__main__":
    if "--test" in sys.argv:
        test()
    else:
        try:
            calistir()
        except Exception:
            logla(traceback.format_exc())
