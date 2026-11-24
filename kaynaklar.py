"""Manga (MangaDex) ve anime (AniList) için son bölüm kaynakları."""
import requests

HEADERS = {"User-Agent": "manga-anime-bildirici/1.0"}

ANILIST_SORGU = """
query ($ad: String, $id: Int) {
  Media(search: $ad, id: $id, type: ANIME) {
    siteUrl episodes title { romaji english } nextAiringEpisode { episode }
    relations { edges { relationType node { id type format status } } }
  }
}"""

DIZI_FORMATLARI = {"TV", "TV_SHORT", "ONA"}


def devam_sezonu(veri: dict) -> int | None:
    """Yayına girmiş TV devam sezonunun id'si (arama hep 1. sezonu bulur)."""
    m = (veri.get("data") or {}).get("Media") or {}
    for e in (m.get("relations") or {}).get("edges", []):
        n = e["node"]
        if (e["relationType"] == "SEQUEL" and n["type"] == "ANIME"
                and n["format"] in DIZI_FORMATLARI and n["status"] != "NOT_YET_RELEASED"):
            return n["id"]
    return None


def _sade(s: str) -> str:
    return "".join(c for c in s.casefold() if c.isalnum())


def manga_baslik_ayikla(veri: dict, ad: str = "") -> dict | None:
    """/manga cevabından {"id", "baslik"} çıkarır.

    Başlığı/alternatif başlığı `ad` ile birebir eşleşen ilk eser seçilir
    (doujinshi/renkli sürüm gibi yan eserler alakada öne geçebiliyor); yoksa ilk sonuç.
    """
    if not veri.get("data"):
        return None
    hedef = _sade(ad)
    m = next((m for m in veri["data"] if hedef and any(
        _sade(v) == hedef for t in [m["attributes"]["title"], *m["attributes"].get("altTitles", [])]
        for v in t.values())), veri["data"][0])
    t = m["attributes"]["title"]
    baslik = t.get("en") or next(iter(t.values()), None)
    return {"id": m["id"], "baslik": baslik} if baslik else None


def manga_bolum_ayikla(veri: dict) -> tuple[str, str] | None:
    """/manga/{id}/feed cevabından (bolum, chapter_id) çıkarır.

    MangaDex chapter'ı metin olarak sıralar: "Extra" gibi sayısal olmayanlar
    desc sıralamada en üste çıkar (null'lar en alta). Bu yüzden en büyük sayısal
    bölüm seçilir; eşitlikte (farklı dil/çeviri) kararlılık için en küçük id.
    """
    if not veri.get("data"):
        return None
    sayisal = []
    for b in veri["data"]:
        try:
            sayisal.append((-float(b["attributes"].get("chapter")), b["id"], b["attributes"]["chapter"]))
        except (TypeError, ValueError):
            pass
    if sayisal:
        _, cid, bolum = min(sayisal)
        return (bolum, cid)
    # Hiç numaralı kayıt yoksa (oneshot) ilk kayıt "Oneshot" olarak döner.
    return ("Oneshot", veri["data"][0]["id"])


def anime_ayikla(veri: dict) -> dict | None:
    """AniList cevabından sonuç dict'i üretir."""
    m = (veri.get("data") or {}).get("Media")
    if not m:
        return None
    sonraki = (m.get("nextAiringEpisode") or {}).get("episode")
    bolum = sonraki - 1 if sonraki else m.get("episodes")
    baslik = m["title"].get("romaji") or m["title"].get("english")
    if not bolum or bolum < 1 or not baslik:
        return None
    return {"baslik": baslik, "bolum": str(bolum), "url": m["siteUrl"]}


def son_manga_bolumu(ad: str) -> dict | None:
    r = requests.get("https://api.mangadex.org/manga",
                     params={"title": ad, "limit": 10, "order[relevance]": "desc"},
                     headers=HEADERS, timeout=15)
    r.raise_for_status()
    manga = manga_baslik_ayikla(r.json(), ad)
    if not manga:
        return None
    # shortcut: ilk 100 kayıtta numaralı bölüm aranır; 100+ ekstra/çeviri üst üste binerse sayfalama gerekir.
    r = requests.get(f"https://api.mangadex.org/manga/{manga['id']}/feed",
                     params={"order[chapter]": "desc", "limit": 100,
                             "translatedLanguage[]": ["en", "tr"]},
                     headers=HEADERS, timeout=15)
    r.raise_for_status()
    bolum = manga_bolum_ayikla(r.json())
    if not bolum:
        return None
    return {"baslik": manga["baslik"], "bolum": bolum[0],
            "url": f"https://mangadex.org/chapter/{bolum[1]}"}


def son_anime_bolumu(ad: str) -> dict | None:
    degiskenler = {"ad": ad}
    for _ in range(10):  # sezon zinciri; sonsuz döngü koruması
        r = requests.post("https://graphql.anilist.co",
                          json={"query": ANILIST_SORGU, "variables": degiskenler},
                          headers=HEADERS, timeout=15)
        # Bulunamayınca AniList 404 döner; bu "yok" demektir, ağ hatası değil.
        if r.status_code == 404:
            return None
        r.raise_for_status()
        veri = r.json()
        sonraki = devam_sezonu(veri)
        if not sonraki:
            break
        degiskenler = {"id": sonraki}
    return anime_ayikla(veri)


if __name__ == "__main__":
    assert manga_baslik_ayikla({"data": []}) is None
    assert manga_baslik_ayikla({"data": [{"id": "x", "attributes": {"title": {"ja-ro": "Naruto"}}}]}) == {"id": "x", "baslik": "Naruto"}
    assert manga_baslik_ayikla({"data": [{"id": "x", "attributes": {"title": {"ja-ro": "A", "en": "B"}}}]})["baslik"] == "B"
    assert manga_bolum_ayikla({"data": []}) is None
    assert manga_bolum_ayikla({"data": [{"id": "c1", "attributes": {"chapter": "1100"}}]}) == ("1100", "c1")
    assert manga_bolum_ayikla({"data": [{"id": "c2", "attributes": {"chapter": None}}]}) == ("Oneshot", "c2")
    # Gerçek ağda görülen sıra: "Extra" en üstte, null en altta; en büyük sayı seçilmeli.
    assert manga_bolum_ayikla({"data": [{"id": "e", "attributes": {"chapter": "Extra"}}, {"id": "a", "attributes": {"chapter": "169"}},
                                        {"id": "b", "attributes": {"chapter": "168.5"}}, {"id": "n", "attributes": {"chapter": None}}]}) == ("169", "a")
    # Aynı bölümün birden çok çevirisi: sıradan bağımsız aynı kayıt.
    iki = [{"id": "z", "attributes": {"chapter": "10"}}, {"id": "y", "attributes": {"chapter": "10"}}]
    assert manga_bolum_ayikla({"data": iki}) == manga_bolum_ayikla({"data": iki[::-1]}) == ("10", "y")
    asil = {"id": "asil", "attributes": {"title": {"ja-ro": "Chainsaw Man"}, "altTitles": []}}
    renkli = {"id": "renkli", "attributes": {"title": {"en": "Chainsaw Man (Official Colored)"}, "altTitles": []}}
    spy = {"id": "spy", "attributes": {"title": {"en": "SPY×FAMILY"}, "altTitles": [{"en": "Spy x Family"}]}}
    assert manga_baslik_ayikla({"data": [renkli, asil]}, "chainsaw man")["id"] == "asil"
    assert manga_baslik_ayikla({"data": [renkli, spy]}, "Spy x Family")["id"] == "spy"
    assert manga_baslik_ayikla({"data": [renkli, asil]}, "bulunmayan")["id"] == "renkli"
    t = {"romaji": "Boku", "english": None}
    assert anime_ayikla({"data": {"Media": {"siteUrl": "u", "episodes": 12, "title": t, "nextAiringEpisode": {"episode": 5}}}}) == {"baslik": "Boku", "bolum": "4", "url": "u"}
    assert anime_ayikla({"data": {"Media": {"siteUrl": "u", "episodes": 12, "title": t, "nextAiringEpisode": None}}})["bolum"] == "12"
    assert anime_ayikla({"data": {"Media": {"siteUrl": "u", "episodes": None, "title": t, "nextAiringEpisode": {"episode": 1}}}}) is None
    assert anime_ayikla({"data": {"Media": None}}) is None
    kenar = lambda r, f, s, i: {"relationType": r, "node": {"id": i, "type": "ANIME", "format": f, "status": s}}
    assert devam_sezonu({"data": {"Media": {"relations": {"edges": [
        kenar("SEQUEL", "MOVIE", "FINISHED", 1), kenar("PREQUEL", "TV", "FINISHED", 2),
        kenar("SEQUEL", "TV", "NOT_YET_RELEASED", 3), kenar("SEQUEL", "TV", "RELEASING", 4)]}}}}) == 4
    assert devam_sezonu({"data": {"Media": {"relations": {"edges": []}}}}) is None
    print("OK")
