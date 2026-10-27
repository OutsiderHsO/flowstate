import { defineConfig } from 'astro/config';

// https://docs.astro.build/en/reference/configuration-reference/

// The public URL of the deployed site. Used for canonical links, hreflang
// alternates and Open Graph tags — if this is wrong, shared links point at
// the wrong host.
//
// Set DEPLOY_URL in Cloudflare's build environment to override it without
// editing code. Falls back to the Cloudflare Pages URL below.
const site = process.env.DEPLOY_URL ?? 'https://flowstate.pages.dev';

export default defineConfig({
  site,
  trailingSlash: 'always',
  build: {
    format: 'directory',
  },
  markdown: {
    shikiConfig: {
      theme: 'github-dark-dimmed',
      wrap: true,
    },
    // Keep CJK line breaking readable in long prose.
    smartypants: false,
  },
  vite: {
    ssr: {
      /**
       * Astro evaluates content-collection modules inside Vite's ESM module
       * runner. `yaml@2.9` maps its `node` export condition to a CommonJS
       * build, so the runner hits `require is not defined`. Keeping it
       * external lets Node resolve it natively (which works).
       */
      external: ['yaml'],
    },
  },
});
