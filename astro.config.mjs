import { defineConfig } from 'astro/config';

// https://docs.astro.build/en/reference/configuration-reference/
export default defineConfig({
  // TODO: set to your real deployment URL before publishing (SEO / canonical links).
  site: 'https://example.github.io',
  trailingSlash: 'always',
  build: {
    format: 'directory',
  },
  markdown: {
    shikiConfig: {
      theme: 'github-dark-dimmed',
      wrap: true,
    },
  },
  vite: {
    ssr: {
      /**
       * Astro 7's content-collection loader evaluates modules inside Vite's
       * ESM module runner. `yaml@2.9` maps its `node` export condition to a
       * CommonJS build, so the runner hits `require is not defined`.
       * Keeping it external lets Node resolve it natively (which works).
       */
      external: ['yaml'],
    },
  },
});
