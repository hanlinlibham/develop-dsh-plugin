import { defineConfig } from 'tsdown'

export default defineConfig({
  entry: { index: 'src/index.ts' },
  outDir: 'lib',
  format: 'esm',
  platform: 'node',
  target: 'node22',
  dts: false,
  sourcemap: true,
  clean: true,
  external: [/^@deepseek-ai\//, /^node:/],
})
