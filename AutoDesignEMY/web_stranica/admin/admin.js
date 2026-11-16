/* Admin: preview, drag & drop, video poster capture, upload progress */
(function () {
  var form = document.getElementById('upload-form');
  if (!form) return;
  var input = document.getElementById('file'), drop = document.getElementById('drop'), text = document.getElementById('drop-text');
  var preview = document.getElementById('preview'), poster = document.getElementById('poster');
  var bar = document.getElementById('progress'), btn = document.getElementById('upload-btn');
  var posterReady = Promise.resolve();

  function capturePoster(file) {
    return new Promise(function (resolve) {
      var v = document.createElement('video'), url = URL.createObjectURL(file), done = false;
      v.muted = true; v.playsInline = true; v.preload = 'auto'; v.src = url;
      function finish() { if (!done) { done = true; URL.revokeObjectURL(url); resolve(); } }
      v.addEventListener('loadeddata', function () { v.currentTime = Math.min(1, (v.duration || 2) / 3); });
      v.addEventListener('seeked', function () {
        try {
          var c = document.createElement('canvas'), s = Math.min(1, 720 / v.videoWidth);
          c.width = Math.round(v.videoWidth * s); c.height = Math.round(v.videoHeight * s);
          c.getContext('2d').drawImage(v, 0, 0, c.width, c.height);
          poster.value = c.toDataURL('image/jpeg', 0.85);
          preview.src = poster.value; preview.hidden = false;
        } catch (e) {}
        finish();
      });
      v.addEventListener('error', finish);
      setTimeout(finish, 8000);
    });
  }
  function onFile() {
    var f = input.files[0]; poster.value = ''; preview.hidden = true;
    if (!f) return;
    text.innerHTML = '<b></b><br><small></small>';
    text.querySelector('b').textContent = f.name;
    text.querySelector('small').textContent = (f.size / 1048576).toFixed(1) + ' MB';
    if (f.type.indexOf('image/') === 0) { preview.src = URL.createObjectURL(f); preview.hidden = false; }
    else if (f.type.indexOf('video/') === 0) posterReady = capturePoster(f);
  }
  input.addEventListener('change', onFile);
  ['dragenter', 'dragover'].forEach(function (e) { drop.addEventListener(e, function (ev) { ev.preventDefault(); drop.classList.add('over'); }); });
  ['dragleave', 'drop'].forEach(function (e) { drop.addEventListener(e, function (ev) { ev.preventDefault(); drop.classList.remove('over'); }); });
  drop.addEventListener('drop', function (ev) { if (ev.dataTransfer.files.length) { input.files = ev.dataTransfer.files; onFile(); } });

  form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    if (!input.files.length) { input.click(); return; }
    btn.disabled = true; btn.textContent = 'Šaljem…';
    posterReady.then(function () {
      var xhr = new XMLHttpRequest();
      xhr.open('POST', form.action || 'index.php');
      xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
      bar.hidden = false;
      xhr.upload.onprogress = function (e) { if (e.lengthComputable) bar.value = Math.round(e.loaded / e.total * 100); };
      xhr.onload = function () { location.href = 'index.php'; };
      xhr.onerror = function () { btn.disabled = false; btn.textContent = 'Dodaj u galeriju'; alert('Upload nije uspio. Provjerite internet vezu i pokušajte ponovo.'); };
      xhr.send(new FormData(form));
    });
  });
})();
