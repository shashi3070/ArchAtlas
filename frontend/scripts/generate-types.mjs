/**
 * Generate TypeScript types from the canonical JSON Schemas.
 * Output is committed; CI regenerates and fails on drift.
 * Usage: npm run generate:types
 */
import { compileFromFile } from 'json-schema-to-typescript'
import { mkdirSync, readdirSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const schemasDir = path.resolve(here, '../../schemas')
const outDir = path.resolve(here, '../src/types/generated')

mkdirSync(outDir, { recursive: true })

const options = {
  bannerComment: '',
  additionalProperties: false,
}

const files = readdirSync(schemasDir).filter((f) => f.endsWith('.schema.json'))

for (const file of files) {
  const name = file.replace('.schema.json', '')
  const outputPath = path.join(outDir, `${name}.gen.ts`)
  process.stdout.write(`[types] ${file} -> ${path.relative(process.cwd(), outputPath)}\n`)
  const ts = await compileFromFile(path.join(schemasDir, file), options)
  writeFileSync(outputPath, ts, 'utf8')
}

process.stdout.write(`[types] done: ${files.length} module(s)\n`)
