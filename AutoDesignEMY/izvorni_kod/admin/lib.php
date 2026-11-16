<?php
/* Auto Design EMY – admin helpers. Not accessible from the web (see .htaccess). */
declare(strict_types=1);

const SITE_ROOT = __DIR__ . '/..';
const DATA_FILE = SITE_ROOT . '/data/gallery.json';
const UPLOAD_DIR = SITE_ROOT . '/media/uploads';
const PRIVATE_DIR = __DIR__ . '/private';
const MAX_IMAGE_BYTES = 25 * 1024 * 1024;     // 25 MB
const MAX_VIDEO_BYTES = 200 * 1024 * 1024;    // 200 MB (also limited by .user.ini / hosting)
const CATS = ['wheels' => 'Volani', 'seats' => 'Sjedišta', 'interior' => 'Unutrašnjost'];

require __DIR__ . '/config.php';

function start_session(): void {
    $secure = !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off';
    session_name('emy_admin');
    session_set_cookie_params(['lifetime' => 0, 'path' => '/', 'secure' => $secure, 'httponly' => true, 'samesite' => 'Strict']);
    session_start();
    if (empty($_SESSION['csrf'])) $_SESSION['csrf'] = bin2hex(random_bytes(32));
}
function is_logged_in(): bool { return !empty($_SESSION['admin']) && ($_SESSION['ua'] ?? '') === ($_SERVER['HTTP_USER_AGENT'] ?? ''); }
function csrf_field(): string { return '<input type="hidden" name="csrf" value="' . h($_SESSION['csrf']) . '">'; }
function check_csrf(): void {
    if (!hash_equals($_SESSION['csrf'] ?? '', (string)($_POST['csrf'] ?? ''))) { http_response_code(400); exit('Sesija je istekla. Osvježite stranicu i pokušajte ponovo.'); }
}
function h(?string $s): string { return htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8'); }
function flash(string $msg, string $type = 'ok'): void { $_SESSION['flash'] = [$msg, $type]; }
function redirect(string $to = 'index.php'): never {
    // uploads are sent with XMLHttpRequest (progress bar): answer without redirect so the flash message survives
    if (($_SERVER['HTTP_X_REQUESTED_WITH'] ?? '') === 'XMLHttpRequest') { http_response_code(204); exit; }
    header('Location: ' . $to, true, 303); exit;
}

/* ---- login throttling (per IP, file based) ---- */
function attempts_file(): string { if (!is_dir(PRIVATE_DIR)) mkdir(PRIVATE_DIR, 0750, true); return PRIVATE_DIR . '/attempts.json'; }
function too_many_attempts(): bool {
    $f = attempts_file(); $a = is_file($f) ? (json_decode((string)file_get_contents($f), true) ?: []) : [];
    $ip = $_SERVER['REMOTE_ADDR'] ?? '?'; $r = $a[$ip] ?? ['n' => 0, 't' => 0];
    return $r['n'] >= 5 && time() - $r['t'] < 900;
}
function record_attempt(bool $success): void {
    $f = attempts_file(); $a = is_file($f) ? (json_decode((string)file_get_contents($f), true) ?: []) : [];
    $ip = $_SERVER['REMOTE_ADDR'] ?? '?';
    if ($success) unset($a[$ip]);
    else { $r = $a[$ip] ?? ['n' => 0, 't' => 0]; if (time() - $r['t'] > 900) $r['n'] = 0; $a[$ip] = ['n' => $r['n'] + 1, 't' => time()]; }
    file_put_contents($f, json_encode($a), LOCK_EX);
}

/* ---- gallery data (atomic writes) ---- */
function load_items(): array {
    if (!is_file(DATA_FILE)) return [];
    $d = json_decode((string)file_get_contents(DATA_FILE), true);
    return is_array($d) ? $d : [];
}
function save_items(array $items): void {
    $tmp = DATA_FILE . '.tmp';
    $json = json_encode(array_values($items), JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT);
    if ($json === false || file_put_contents($tmp, $json, LOCK_EX) === false || !rename($tmp, DATA_FILE)) {
        throw new RuntimeException('Ne mogu snimiti galeriju (provjerite dozvole za folder /data).');
    }
}
function find_index(array $items, string $id): int {
    foreach ($items as $i => $it) if (($it['id'] ?? '') === $id) return $i;
    return -1;
}

/* ---- image processing (GD) ---- */
function upload_subdir(): string {
    $dir = UPLOAD_DIR . '/' . date('Y');
    if (!is_dir($dir) && !mkdir($dir, 0755, true)) throw new RuntimeException('Ne mogu kreirati folder za upload.');
    return $dir;
}
function load_gd_image(string $path, string $mime) {
    $im = match ($mime) {
        'image/jpeg' => @imagecreatefromjpeg($path),
        'image/png' => @imagecreatefrompng($path),
        'image/webp' => function_exists('imagecreatefromwebp') ? @imagecreatefromwebp($path) : false,
        default => false,
    };
    if (!$im) throw new RuntimeException('Format slike nije podržan. Koristite JPG, PNG ili WebP.');
    if ($mime === 'image/jpeg' && function_exists('exif_read_data')) {
        $exif = @exif_read_data($path);
        $o = (int)($exif['Orientation'] ?? 1);
        if ($o === 3) $im = imagerotate($im, 180, 0);
        elseif ($o === 6) $im = imagerotate($im, -90, 0);
        elseif ($o === 8) $im = imagerotate($im, 90, 0);
    }
    return $im;
}
function save_resized($im, int $maxW, int $maxH, string $base): array {
    $w = imagesx($im); $h = imagesy($im);
    $scale = min(1, $maxW / $w, $maxH / $h);
    $nw = max(1, (int)round($w * $scale)); $nh = max(1, (int)round($h * $scale));
    $dst = imagecreatetruecolor($nw, $nh);
    imagefill($dst, 0, 0, imagecolorallocate($dst, 255, 255, 255));
    imagecopyresampled($dst, $im, 0, 0, 0, 0, $nw, $nh, $w, $h);
    if (function_exists('imagewebp')) { $file = $base . '.webp'; imagewebp($dst, $file, 80); }
    else { $file = $base . '.jpg'; imageinterlace($dst, true); imagejpeg($dst, $file, 82); }
    imagedestroy($dst);
    return [$file, $nw, $nh];
}
function rel(string $abs): string { return ltrim(str_replace(realpath(SITE_ROOT), '', realpath($abs)), '/\\'); }

function placeholder_poster(string $base): string {
    $im = imagecreatetruecolor(720, 1280);
    imagefill($im, 0, 0, imagecolorallocate($im, 28, 29, 32));
    $w = imagecolorallocate($im, 255, 255, 255);
    imagefilledpolygon($im, [320, 560, 320, 720, 440, 640], $w);
    [$f] = save_resized($im, 720, 1280, $base);
    imagedestroy($im);
    return $f;
}

function handle_upload(array $file, array $meta, ?string $posterData): array {
    if (($file['error'] ?? UPLOAD_ERR_NO_FILE) !== UPLOAD_ERR_OK) {
        $map = [UPLOAD_ERR_INI_SIZE => 'Datoteka je prevelika za postavke servera.', UPLOAD_ERR_FORM_SIZE => 'Datoteka je prevelika.',
                UPLOAD_ERR_PARTIAL => 'Upload je prekinut. Pokušajte ponovo.', UPLOAD_ERR_NO_FILE => 'Niste odabrali datoteku.'];
        throw new RuntimeException($map[$file['error'] ?? 4] ?? 'Greška pri uploadu.');
    }
    if (!is_uploaded_file($file['tmp_name'])) throw new RuntimeException('Neispravan upload.');
    $mime = (new finfo(FILEINFO_MIME_TYPE))->file($file['tmp_name']) ?: '';
    $id = date('Ymd-His') . '-' . bin2hex(random_bytes(3));
    $dir = upload_subdir();
    $item = ['id' => $id, 'cat' => $meta['cat'], 'caption' => array_filter(['bs' => $meta['cap_bs'], 'en' => $meta['cap_en']]),
             'featured' => $meta['featured'], 'added' => date('c')];

    if (str_starts_with($mime, 'image/')) {
        if ($file['size'] > MAX_IMAGE_BYTES) throw new RuntimeException('Slika je veća od 25 MB.');
        $im = load_gd_image($file['tmp_name'], $mime);
        [$full, $fw, $fh] = save_resized($im, 1600, 1600, "$dir/$id");
        [$thumb] = save_resized($im, 640, 960, "$dir/$id-thumb");
        imagedestroy($im);
        return $item + ['type' => 'image', 'full' => rel($full), 'thumb' => rel($thumb), 'w' => $fw, 'h' => $fh];
    }
    $videoExt = ['video/mp4' => 'mp4', 'video/webm' => 'webm', 'video/quicktime' => 'mov'];
    if (isset($videoExt[$mime])) {
        if ($file['size'] > MAX_VIDEO_BYTES) throw new RuntimeException('Video je veći od 200 MB.');
        $dest = "$dir/$id." . $videoExt[$mime];
        if (!move_uploaded_file($file['tmp_name'], $dest)) throw new RuntimeException('Ne mogu snimiti video.');
        chmod($dest, 0644);
        $w = 720; $h = 1280;
        if ($posterData && preg_match('#^data:image/(jpeg|png|webp);base64,#', $posterData)) {
            $bin = base64_decode(substr($posterData, strpos($posterData, ',') + 1), true);
            $pim = $bin ? @imagecreatefromstring($bin) : false;
            if ($pim) { [$poster, $w, $h] = save_resized($pim, 720, 1280, "$dir/$id-poster"); imagedestroy($pim); }
        }
        if (empty($poster)) $poster = placeholder_poster("$dir/$id-poster");
        return $item + ['type' => 'video', 'src' => rel($dest), 'thumb' => rel($poster), 'w' => $w, 'h' => $h];
    }
    throw new RuntimeException('Format nije podržan. Slike: JPG, PNG, WebP. Videi: MP4, WebM, MOV.');
}

function delete_item_files(array $it): void {
    $base = realpath(UPLOAD_DIR);
    foreach (['full', 'thumb', 'src'] as $k) {
        if (empty($it[$k])) continue;
        $p = realpath(SITE_ROOT . '/' . $it[$k]);
        // only files the admin uploaded are deleted; original website media stays on disk
        if ($p && $base && str_starts_with($p, $base . DIRECTORY_SEPARATOR) && is_file($p)) @unlink($p);
    }
}
