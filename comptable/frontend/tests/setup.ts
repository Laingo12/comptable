import '@testing-library/jest-dom/vitest';
import { afterEach, vi } from 'vitest';
import { cleanup, configure } from '@testing-library/react';

// Porte l'attente async (findBy*) à 5 s au lieu de 1 s par défaut.
// En suite parallèle (18 fichiers), 1 s ne suffit pas toujours.
configure({ asyncUtilTimeout: 5000 });

afterEach(() => {
  cleanup();
});

// --- Polyfills jsdom ----------------------------------------------------
// Recharts (via ResponsiveContainer) requiert ResizeObserver, absent de jsdom.

class ResizeObserverStub {
  observe(): void { /* no-op */ }
  unobserve(): void { /* no-op */ }
  disconnect(): void { /* no-op */ }
}

if (typeof globalThis.ResizeObserver === 'undefined') {
  // @ts-expect-error — stub minimal suffisant pour les tests
  globalThis.ResizeObserver = ResizeObserverStub;
}

// jsdom renvoie 0 pour ces propriétés → Recharts ne rend rien.
Object.defineProperty(HTMLElement.prototype, 'clientWidth', {
  configurable: true,
  get() { return 800; },
});
Object.defineProperty(HTMLElement.prototype, 'clientHeight', {
  configurable: true,
  get() { return 400; },
});

// matchMedia est requis par certains composants responsive.
if (typeof window !== 'undefined' && !window.matchMedia) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
}