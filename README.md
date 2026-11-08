# product-image-batch

Příprava produktových fotek pro e-shop v jedné dávce: oříznutí prázdného okraje,
doplnění na čtverec bílým pozadím, zmenšení na jednotný rozměr, převod do JPEG,
odstranění EXIF a manifest pro import.

Běží lokálně (Pillow), bez cloudu a bez API klíčů — fotky neopouští počítač.

## Proč

E-shop s 300 SKU dostane od dodavatele fotky v pěti různých rozměrech, s šedým
nebo průhledným pozadím a s EXIF daty. Ruční úprava v Photoshopu je hodiny práce,
která se opakuje při každé nové kolekci. Tohle je deterministický krok před importem.

## Použití

```bash
python -m img_batch run --in photos --out out --size 1600 --format jpg --quality 90
```

Výstup: `out/<sku>_01.jpg` … a `out/manifest.csv`:

```
source,output,width,height,bytes,status
photos/FOA-110.jpg,out/FOA-110_01.jpg,1600,1600,182341,ok
```

Exit kód `2`, pokud některý soubor selhal (poškozený obrázek, nepodporovaný formát).

## Co dělá

| Krok | Detail |
|---|---|
| ořez | najde bounding box produktu vůči bílému pozadí (práh `--threshold`, výchozí 245) |
| čtverec | doplní okraje bílou (nebo `--bg` barvou), aby poměr stran byl 1:1 |
| resize | LANCZOS na přesný rozměr `--size` (výchozí 1600×1600) |
| průhlednost | PNG s alfou se zploští na bílé pozadí (e-shop konvence) |
| metadata | EXIF/ICC pryč, JPEG progressive, kvalita `--quality` |
| manifest | CSV se skutečnými rozměry a velikostí pro kontrolu importu |

## Bezpečnost

- nikdy nepřepisuje vstupní soubory (výstup jde do `--out`);
- `--dry-run` jen spočítá, co by udělal;
- pokud je obrázek menší než cíl, **nezvětšuje** ho (rozmazání) — jen doplní
  pozadí a nechá `warn` v manifestu.

## Testy

```bash
python -m unittest discover -s tests -v
```

MIT licencováno.

## Poznámka ke vzniku

Téma vychází z diskusí, kde obchodníci zmiňují ruční úpravu fotek jako
opakovanou ztrátu času před každým importem. Kód je vlastní implementace.
