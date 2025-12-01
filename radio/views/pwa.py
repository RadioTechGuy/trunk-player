"""
Trunk Player v2 - PWA Views

Views for Progressive Web App manifest and service worker.
"""

import json

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET


@require_GET
@cache_page(60 * 60)  # Cache for 1 hour
def manifest(request):
    """Return PWA manifest."""
    manifest_data = {
        "name": settings.SITE_TITLE,
        "short_name": settings.SITE_TITLE[:12],
        "description": "Radio transmission player and scanner",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0f172a",
        "theme_color": "#1e293b",
        "orientation": "any",
        "icons": [
            {
                "src": "/static/icons/icon-72.png",
                "sizes": "72x72",
                "type": "image/png",
            },
            {
                "src": "/static/icons/icon-96.png",
                "sizes": "96x96",
                "type": "image/png",
            },
            {
                "src": "/static/icons/icon-128.png",
                "sizes": "128x128",
                "type": "image/png",
            },
            {
                "src": "/static/icons/icon-144.png",
                "sizes": "144x144",
                "type": "image/png",
            },
            {
                "src": "/static/icons/icon-152.png",
                "sizes": "152x152",
                "type": "image/png",
            },
            {
                "src": "/static/icons/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable",
            },
            {
                "src": "/static/icons/icon-384.png",
                "sizes": "384x384",
                "type": "image/png",
            },
            {
                "src": "/static/icons/icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
            },
        ],
        "categories": ["utilities", "entertainment"],
        "screenshots": [],
        "shortcuts": [
            {
                "name": "Listen Live",
                "short_name": "Live",
                "description": "Listen to live transmissions",
                "url": "/scan/default/",
                "icons": [{"src": "/static/icons/icon-96.png", "sizes": "96x96"}],
            },
            {
                "name": "Talkgroups",
                "short_name": "TGs",
                "description": "Browse talkgroups",
                "url": "/talkgroups/",
                "icons": [{"src": "/static/icons/icon-96.png", "sizes": "96x96"}],
            },
        ],
    }

    return JsonResponse(manifest_data)


@require_GET
@cache_page(60 * 60 * 24)  # Cache for 24 hours
def service_worker(request):
    """Return service worker JavaScript."""
    sw_js = """
// Trunk Player Service Worker
const CACHE_NAME = 'trunk-player-v1';
const STATIC_CACHE = 'trunk-player-static-v1';

const STATIC_ASSETS = [
    '/',
    '/static/css/app.css',
    '/static/js/app.js',
];

// Install event
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => cache.addAll(STATIC_ASSETS))
            .then(() => self.skipWaiting())
    );
});

// Activate event
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME && name !== STATIC_CACHE)
                    .map((name) => caches.delete(name))
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch event
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Don't cache API requests or WebSocket
    if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws/')) {
        return;
    }

    // Network-first for HTML pages
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request)
                .then((response) => {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, responseClone);
                    });
                    return response;
                })
                .catch(() => caches.match(event.request))
        );
        return;
    }

    // Cache-first for static assets
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.match(event.request)
                .then((response) => {
                    if (response) {
                        return response;
                    }
                    return fetch(event.request).then((response) => {
                        const responseClone = response.clone();
                        caches.open(STATIC_CACHE).then((cache) => {
                            cache.put(event.request, responseClone);
                        });
                        return response;
                    });
                })
        );
        return;
    }

    // Network-first for everything else
    event.respondWith(
        fetch(event.request)
            .then((response) => response)
            .catch(() => caches.match(event.request))
    );
});

// Push notification handling
self.addEventListener('push', (event) => {
    if (!event.data) return;

    const data = event.data.json();
    const options = {
        body: data.body,
        icon: '/static/icons/icon-192.png',
        badge: '/static/icons/icon-72.png',
        vibrate: [100, 50, 100],
        data: {
            url: data.url || '/',
        },
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});
"""
    return HttpResponse(sw_js, content_type="application/javascript")
