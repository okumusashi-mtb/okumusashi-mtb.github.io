import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  site: 'https://okumusashi-mtb.github.io',
  base: '/',
  trailingSlash: 'always',
  vite: { plugins: [tailwindcss()] },
});
