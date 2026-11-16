# Auto Design EMY – web stranica

## Šta je u paketu

- **web_stranica/** – gotova stranica, spremna za upload na hosting (sve u ovom folderu ide u `public_html`).
- **izvorni_kod/** – izvorni fajlovi za buduće izmjene teksta i dizajna (`build.py`, `src/`, `admin/`).

## Tehnologija

- Statične HTML stranice (11 jezika, 55 stranica) + jedan CSS i jedan JavaScript fajl, bez vanjskih biblioteka.
- Fontovi su na serveru (bez Google Fonts poziva), slike su u WebP formatu s JPG rezervom.
- Admin panel je u PHP-u, **bez baze podataka** – galerija se čuva u `data/gallery.json`.
- Radi na običnom (jeftinom) shared hostingu sa Apache serverom i PHP 8.1 ili novijim (GD ekstenzija – standardno uključena).

## Postavljanje na hosting

1. Uploadujte **sadržaj** foldera `web_stranica/` u `public_html` (uključujući skrivene `.htaccess` fajlove).
2. Folderima `data/` i `media/uploads/` dajte dozvolu za pisanje (obično 755; ako upload ne radi, 775).
3. Otvorite `https://vaš-domen/admin/` i prijavite se (podaci su poslani odvojeno). **Odmah promijenite lozinku** (dno admin stranice).
4. Kad dobijete domen, u izvornom kodu pokrenite:
   `SITE_URL=https://www.vaš-domen.ba python3 build.py`
   To dodaje canonical/hreflang linkove i `sitemap.xml`. Zatim ponovo uploadujte sve **osim** `data/gallery.json` i `media/uploads/` (da ne prepišete radove dodane kroz admin).
5. Prijavite stranicu u Google Search Console i otvorite/ažurirajte Google Business profil sa istom adresom i telefonom.

## Admin panel (`/admin/`)

- Ne postoji link na stranici; pretraživači ga ne indeksiraju (`robots.txt`, `noindex`).
- Dodavanje slika (JPG, PNG, WebP do 25 MB) i videa (MP4 preporučeno, do 200 MB).
  Slike se automatski smanjuju i pretvaraju u WebP. Za video se naslovna slika pravi automatski u pregledniku.
- Kategorija (Volani / Sjedišta / Unutrašnjost), opis na bosanskom i engleskom, ★ za prikaz na početnoj (prvih 6).
- Redoslijed (na vrh / gore / dole), izmjena, brisanje.
- Zaštita: lozinka (hash), CSRF zaštita, blokada nakon 5 pogrešnih pokušaja (15 min), uploadovani fajlovi se ne mogu izvršavati.
- Video sa iPhonea (MOV/HEVC) možda neće raditi u svim preglednicima – najsigurnije je MP4.

## Kontakt funkcionalnost

Firma nema email, pa kontakt forma **otvara WhatsApp** s već pripremljenom porukom (ime, vozilo, usluga, poruka).
Dugme „kopiraj poruku za Viber“ kopira isti tekst i otvara Viber. Na svakoj stranici su i dugmad Pozovi / WhatsApp / Viber.

## Izmjena tekstova

Svi tekstovi su u `src/i18n/<jezik>.json` (bs, en, de, fr, tr, ar, it, sv, ru, sq, mk).
Nakon izmjene: `python3 build.py` → novi `dist/` folder → upload (osim `data/` i `media/uploads/`).

## Napomene

- Prevode na 10 stranih jezika preporučujemo da pregleda izvorni govornik prije objave.
- Brojevi na Instagramu (440+ objava, 2.200+ pratilaca) su iz novembra 2026. i nalaze se u `build.py` i prevodima.
- Logo na stranici je tekstualna verzija; kada dobijemo originalni logo fajl (SVG/PNG), zamijenićemo ga.
