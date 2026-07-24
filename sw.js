// 詐欺電話撃退アプリ – サービスワーカー（スマホアプリ化用）
const CACHE = 'sagi-keikoku-v6';
const SHARE_CACHE = 'sagi-keikoku-share';
const SHARE_KEY = 'shared-audio-file';
const SHELL = ['./', 'index.html', 'manifest.json', 'icon-192.png', 'icon-512.png', 'news_data.js', 'curated_news.js'];

self.addEventListener('install', (e) => {
  self.skipWaiting();
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(SHELL).catch(() => {}))
  );
});

self.addEventListener('activate', (e) => {
  self.clients.claim();
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE && k !== SHARE_CACHE).map((k) => caches.delete(k)))
    )
  );
});

// 電話アプリなどの「共有」から音声ファイルが送られてきた時の受け口
async function handleShare(e) {
  const formData = await e.request.formData();
  const file = formData.get('file');
  if (!file) return;

  const headers = {
    'Content-Type': file.type || 'application/octet-stream',
    'X-Shared-Filename': encodeURIComponent(file.name || '共有された録音')
  };
  const cache = await caches.open(SHARE_CACHE);
  await cache.put(SHARE_KEY, new Response(file, { headers }));

  // 遷移先のウィンドウが確定していれば、すぐにメッセージで知らせる（ページ側は
  // ?shared=1 での起動チェックとpostMessageの両方を見て、どちらか先に来た方で拾う）
  const client = await self.clients.get(e.resultingClientId).catch(() => null);
  if (client) client.postMessage({ type: 'shared-file-ready' });
}

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method === 'POST' && url.pathname.endsWith('/share-target/')) {
    e.respondWith(Response.redirect('./?shared=1', 303));
    e.waitUntil(handleShare(e).catch(() => {}));
    return;
  }

  if (url.origin !== self.location.origin) {
    return;
  }
  e.respondWith(
    fetch(e.request)
      .then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
        return res;
      })
      .catch(() => caches.match(e.request))
  );
});
