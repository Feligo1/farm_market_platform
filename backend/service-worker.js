// service-worker.js
// FarmConnect PWA Service Worker
// Provides offline support and push notifications

const CACHE_NAME = 'farmconnect-v1';
const STATIC_CACHE = 'farmconnect-static-v1';
const DYNAMIC_CACHE = 'farmconnect-dynamic-v1';

// Assets to cache for offline access
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/dashboard.html',
  '/market-prices.html',
  '/price-forecast.html',
  '/find-buyers.html',
  '/profile.html',
  '/register.html',
  '/offline.html',
  '/manifest.json',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap',
  'https://cdn.jsdelivr.net/npm/chart.js'
];

// API endpoints to cache
const API_CACHE_ENDPOINTS = [
  '/api/status',
  '/api/markets',
  '/api/prices/real'
];

// Install event - cache static assets
self.addEventListener('install', event => {
  console.log('[Service Worker] Installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('[Service Worker] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('[Service Worker] Activating...');
  
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cache => {
          if (cache !== STATIC_CACHE && cache !== DYNAMIC_CACHE) {
            console.log('[Service Worker] Deleting old cache:', cache);
            return caches.delete(cache);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  
  // Handle API requests
  if (url.pathname.startsWith('/api/')) {
    // For API requests, try network first, then cache
    event.respondWith(
      fetch(event.request)
        .then(response => {
          // Cache successful API responses
          if (response.status === 200 && API_CACHE_ENDPOINTS.some(api => url.pathname.includes(api))) {
            const clonedResponse = response.clone();
            caches.open(DYNAMIC_CACHE).then(cache => {
              cache.put(event.request, clonedResponse);
            });
          }
          return response;
        })
        .catch(() => {
          // Offline: serve from cache
          return caches.match(event.request);
        })
    );
  } 
  // Handle static assets
  else if (STATIC_ASSETS.some(asset => url.pathname === asset || url.href.includes(asset))) {
    event.respondWith(
      caches.match(event.request)
        .then(response => {
          return response || fetch(event.request);
        })
    );
  }
  // Handle HTML pages - network first with offline fallback
  else if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .catch(() => {
          return caches.match('/offline.html');
        })
    );
  }
  // Handle other requests
  else {
    event.respondWith(
      caches.match(event.request)
        .then(response => {
          return response || fetch(event.request);
        })
    );
  }
});

// Push Notification event
self.addEventListener('push', event => {
  console.log('[Service Worker] Push received:', event);
  
  let data = {
    title: 'FarmConnect Zambia',
    body: 'New market update available!',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/badge.png',
    tag: 'farmconnect-update',
    data: {
      url: '/market-prices.html'
    }
  };
  
  if (event.data) {
    try {
      data = JSON.parse(event.data.text());
    } catch (e) {
      data.body = event.data.text();
    }
  }
  
  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: data.icon,
      badge: data.badge,
      tag: data.tag,
      data: data.data,
      actions: [
        {
          action: 'open',
          title: 'View Details'
        },
        {
          action: 'dismiss',
          title: 'Dismiss'
        }
      ],
      vibrate: [200, 100, 200],
      requireInteraction: true
    })
  );
});

// Notification click event
self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  if (event.action === 'dismiss') {
    return;
  }
  
  const urlToOpen = event.notification.data?.url || '/';
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then(windowClients => {
        // Check if there's already a window/tab open with the target URL
        for (let client of windowClients) {
          if (client.url === urlToOpen && 'focus' in client) {
            return client.focus();
          }
        }
        // If not, open a new window
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});

// Background Sync for offline price submissions
self.addEventListener('sync', event => {
  console.log('[Service Worker] Sync event:', event);
  
  if (event.tag === 'sync-prices') {
    event.waitUntil(syncOfflinePrices());
  }
});

async function syncOfflinePrices() {
  const cache = await caches.open(DYNAMIC_CACHE);
  const requests = await cache.keys();
  
  for (const request of requests) {
    if (request.url.includes('/api/prices')) {
      try {
        const response = await fetch(request);
        if (response.ok) {
          await cache.delete(request);
          console.log('[Service Worker] Synced offline price:', request.url);
        }
      } catch (error) {
        console.log('[Service Worker] Sync failed:', error);
      }
    }
  }
}