const CACHE_NAME = 'flower-detector-v1';
const OFFLINE_URL = '/offline';

// Fichiers essentiels à mettre en cache
const urlsToCache = [
  '/',  // Page d'accueil
  '/offline/',  // Page hors ligne
  '/static/manifest.json',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png'
];

// Installation
self.addEventListener('install', event => {
  console.log('📦 Service Worker: Installation...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('✅ Cache ouvert');
        return cache.addAll(urlsToCache);
      })
      .then(() => {
        console.log('🎯 Tous les fichiers en cache');
        return self.skipWaiting();
      })
  );
});

// Activation
self.addEventListener('activate', event => {
  console.log('🚀 Service Worker: Activation...');
  
  event.waitUntil(
    Promise.all([
      // Nettoyer les anciens caches
      caches.keys().then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== CACHE_NAME) {
              console.log('🗑️ Suppression ancien cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      }),
      // Prendre le contrôle immédiat
      self.clients.claim()
    ])
  );
});

// Interception des requêtes
self.addEventListener('fetch', event => {
  // Ignorer les requêtes non-GET
  if (event.request.method !== 'GET') return;
  
  // Pour les requêtes HTML, utiliser "network first, then cache, then offline page"
  if (event.request.headers.get('accept').includes('text/html')) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          // Mettre à jour le cache avec la nouvelle réponse
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, responseClone);
          });
          return response;
        })
        .catch(() => {
          // Si le réseau échoue, chercher dans le cache
          return caches.match(event.request)
            .then(cachedResponse => {
              if (cachedResponse) {
                return cachedResponse;
              }
              // Si pas dans le cache, retourner la page offline
              return caches.match(OFFLINE_URL);
            });
        })
    );
    return;
  }
  
  // Pour les autres ressources (CSS, JS, images), utiliser "cache first"
  event.respondWith(
    caches.match(event.request)
      .then(cachedResponse => {
        if (cachedResponse) {
          return cachedResponse;
        }
        
        return fetch(event.request)
          .then(response => {
            // Mettre en cache pour la prochaine fois
            const responseClone = response.clone();
            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseClone);
              });
            return response;
          })
          .catch(() => {
            // Pour les images, retourner une icône par défaut si hors ligne
            if (event.request.destination === 'image') {
              return caches.match('/static/icons/icon-192x192.png');
            }
            return new Response('Ressource non disponible hors ligne', {
              status: 408,
              headers: { 'Content-Type': 'text/plain' }
            });
          });
      })
  );
});