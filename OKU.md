# Changelog yazma kılavuzu

Bu klasördeki dosyalar **Tebex'e yüklenmez.** `github.com/CylexVII/changelog` reposunun köküne gider.

```
CylexVII/changelog/
  index.json
  cylex_phone.json
  cylex_housingv2.json
  cylex_mdt.json
  ...
```

Commit attığın an site güncellenir. GitHub'ın CDN'i ~5 dakika cache tuttuğu için hemen değil, birkaç dakika içinde.

Sürüm kontrolü ayrı repoda: `CylexVII/versionchecker/<resource>.txt`. Orası çıplak sürüm numarası, `update.lua` onu okuyor — karıştırma.

---

## Dosya adı

Dosya adı = FiveM resource adı = paket açıklamasındaki `CYLEX_SCRIPT` değeri. Üçü aynı olmak zorunda.

`cylex_housingv2` → `cylex_housingv2.json`

---

## Bir changelog dosyası

```json
{
  "package": "Cylex Housing v2",
  "entries": [
    {
      "version": "1.13",
      "date": "2026-09-01",
      "title": "Shell placement & performance",
      "images": [
        "https://i.imgur.com/abc123.png"
      ],
      "files": ["client", "server", "html"],
      "changes": [
        { "type": "add",    "text": "12 new interior shells have been added" },
        { "type": "fix",    "text": "Players no longer clip into the floor when opening a door" },
        { "type": "perf",   "text": "The property list now opens 3x faster" },
        { "type": "change", "text": "Changed files: client, server, html" },
        { "type": "remove", "text": "The old /househelp command has been removed" }
      ]
    }
  ]
}
```

### Alanlar

| Alan | Zorunlu | Açıklama |
|---|---|---|
| `package` | evet | Sayfada görünen ad |
| `entries` | evet | Sürümler, **yeniden eskiye** sıralı |
| `version` | evet | `1.13` — fxmanifest'teki sürümle aynı olsun |
| `date` | evet | `YYYY-AA-GG` |
| `title` | hayır | Sürümün tek cümlelik özeti, İngilizce. `"UPDATE 1.13"` gibi sürümü tekrarlayan başlık yazma, boş bırak |
| `images` | hayır | Görsel adresleri. UI değişikliklerinde ekran görüntüsü koy |
| `files` | hayır | Müşterinin güncellemesi gereken dosya/klasörler |
| `changes` | evet | Değişiklik satırları |
| `type` | evet | Aşağıdaki beş değerden biri |
| `text` | evet | Değişikliğin kendisi |

Güncel sürüm ayrıca yazılmıyor — listedeki **en üstteki** kayıt güncel sürüm sayılıyor.

### type değerleri

| type | Rozet | Renk | Ne zaman |
|---|---|---|---|
| `add` | NEW | yeşil | Yeni özellik, yeni içerik |
| `fix` | FIX | turuncu | Düzeltilen hata |
| `perf` | PERF | mavi | Hız, optimizasyon |
| `change` | CHANGED | gri | Değişen davranış, değişen dosyalar |
| `remove` | REMOVED | kırmızı | Kaldırılan şey |

---

## files — değişen dosyalar

Zorunlu değil ama **koy**. Müşteri güncellemeyi indirince neyi değiştireceğini bilmesi gerekiyor; yoksa hepsini elle karşılaştırıyor.

```json
"files": ["client", "server", "html", "fxmanifest.lua"]
```

Dosya adının yanına parantez içinde not düşebilirsin. Parantezli kısım sayfada dosya adından ayrı, soluk yazıyla çıkıyor:

```json
"files": ["html (remove the old html folder and replace it)", "server", "locales"]
```

Sayfada sürümün en üstünde katlanır bir kutuda duruyor; açınca resource adının altında ağaç görünümünde listeleniyor. Not da İngilizce olacak.

---

## images — ekran görüntüleri

UI değişikliklerinde ekran görüntüsü koy. Zorunlu değil.

```json
"images": [
  "https://i.imgur.com/abc123.png",
  "https://i.imgur.com/def456.png"
]
```

Doğrudan görsele giden adres olmalı (`.png`, `.jpg`, `.jpeg`, `.webp`). Imgur veya fivemanage olur; imgur'da **paylaşım sayfası değil** görselin kendi adresi lazım (`i.imgur.com/...` ile başlayan).

Sayfada değişiklik listesinin **altında**, 16:10 küçük kareler halinde ızgara olarak çıkıyor. Tıklayınca sayfa içinde tam ekran açılıyor; boş alana tıklayarak, sağ üstteki çarpıyla veya Esc ile kapanıyor.

---

## Dil: her zaman İngilizce

`package`, `title` ve `text` alanlarının **hepsi İngilizce** yazılır. Müşteri kitlesi uluslararası, sayfanın geri kalanı da İngilizce. Türkçe satır girme — ne changelog metnine, ne başlığa.

Bu dosyanın kendisi Türkçe, o ayrı; kılavuz sana yazılmış, changelog müşteriye.

## İyi satır nasıl yazılır

Kullanıcının gördüğü davranışı anlat, kod terimi kullanma.

Kötü:
```
"Bug fix"
"Optimization"
"Fixed NUI callback"
```

İyi:
```
"The \"Inventory Full\" notification no longer appears when the inventory is empty"
"Holding the capture button no longer uploads the same photo multiple times"
"The property list now opens without stuttering on servers with 200+ houses"
```

Uzun sürümlerde konu başlığı ekleyebilirsin:
```
"Messages: Read receipts have been added"
"Garage: The valet can now be disabled from the config"
```

---

## Yeni sürüm eklerken

1. İlgili dosyayı aç
2. `entries` dizisinin **en başına** yeni bir kayıt ekle
3. `versionchecker` reposundaki `<resource>.txt` dosyasını da aynı sürüme güncelle
4. Commit

---

## Yeni script eklerken

1. `<resource>.json` dosyasını oluştur
2. `index.json`'a bir satır ekle:

```json
{ "key": "cylex_yenisey", "name": "Cylex Yeni Şey", "packageId": 1234567 }
```

`packageId` isteğe bağlı; yazarsan `/changelog` sayfasında pakete link çıkar, yazmazsan çıkmaz.

3. Paket açıklamasına `CYLEX_SCRIPT: cylex_yenisey` satırını ekle

---

## Claude'a yaptırmak istersen

Bu klasörde çalışırken şöyle şeyler söyleyebilirsin, gerisini halleder:

> cylex_mdt'ye 1.17 sürümü ekle, bugün tarihli. Yeni: olay geçmişi filtresi, plaka arama. Düzeltildi: rapor silinince listede kalması, mobilde tablo taşması.

(Türkçe anlatman sorun değil, İngilizceye çevirip yazar.)

> cylex_phone'un 1.38'ini ekle, changed files client ve html.

> cylex_housingv2 1.14'e şu iki görseli ekle: <adres> <adres>

> Şu metni changelog formatına çevir ve cylex_housing.json'a ekle: <yapıştır>

> index.json'a cylex_banking'i ekle, adı "Cylex Banking", paket id 6180403.

Discord'a attığın güncelleme notunu olduğu gibi yapıştırıp "bunu changelog'a çevir" demen de yeterli — kategorilere ayırıp doğru `type` değerlerini kendisi seçer.

---

## Kontrol

Commit'ten önce dosyanın geçerli JSON olduğundan emin ol:

```bash
python -c "import json;json.load(open('cylex_phone.json',encoding='utf8'));print('ok')"
```

---

## Tek script sayfası

Her script'in kendi adresi var:

```
cylexdev.com/changelog                  hepsi
cylexdev.com/changelog/cylex_phone      sadece telefon
```

Discord'da güncelleme duyurusu atarken script'e özel adresi verebilirsin. `?script=cylex_phone` ve `#cylex_phone` de çalışıyor.

`/changelog` sayfasında script'ler **en son güncellenene göre** sıralı, yeni güncellenen üstte.

---

Sistemin tamamı için: `../CHANGELOG-SISTEMI.md`
