import { FlatCompat } from '@eslint/eslintrc';
import { dirname } from 'path';
import { fileURLToPath } from 'url';

const filePath = fileURLToPath(import.meta.url);
const directoryPath = dirname(filePath);
const compat = new FlatCompat({
  baseDirectory: directoryPath,
});

const eslintConfig = [
  {
    ignores: ['.next/**', 'next-env.d.ts', 'node_modules/**', 'out/**'],
  },
  ...compat.extends('next/core-web-vitals', 'next/typescript'),
];

export default eslintConfig;
