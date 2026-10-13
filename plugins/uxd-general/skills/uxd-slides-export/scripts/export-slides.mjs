#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadDeck, validateDeck } from '../../uxd-slides-create/scripts/parse-slides.mjs';

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const VIEWER_DIR = path.join(SCRIPT_DIR, '..', 'viewer');
const TEMPLATES_DIR = path.join(SCRIPT_DIR, '..', '..', 'uxd-slides-create', 'templates');

function parseArgs(argv) {
  const options = {};
  const positional = [];
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--output') options.output = argv[++index];
    else if (arg === '--title') options.title = argv[++index];
    else if (arg === '--help' || arg === '-h') options.help = true;
    else if (arg.startsWith('--')) throw new Error(`Unknown flag: ${arg}`);
    else positional.push(arg);
  }
  options.input = positional[0];
  if (positional.length > 1) throw new Error(`Unexpected argument: ${positional[1]}`);
  return options;
}

function usage() {
  return [
    'Usage: export-slides.mjs <slides-dir> [--output <dir>] [--title <text>]',
    '',
    'Writes index.html, viewer.css, custom.css, viewer.js, deck.json, slides.md,',
    'metadata.json, assets/, and export-manifest.json.'
  ].join('\n');
}

function jsonForScript(value) {
  return JSON.stringify(value)
    .replace(/</g, '\\u003c')
    .replace(/>/g, '\\u003e')
    .replace(/&/g, '\\u0026')
    .replace(/\u2028/g, '\\u2028')
    .replace(/\u2029/g, '\\u2029');
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function replaceOnce(source, token, replacement) {
  if (!source.includes(token)) throw new Error(`Viewer HTML is missing ${token}.`);
  return source.replace(token, () => replacement);
}

function defaultOutput(inputDir) {
  if (path.basename(inputDir) === 'slides') return path.join(path.dirname(inputDir), 'export');
  return path.join(inputDir, 'export');
}

function copyAssets(sourceDir, outputDir) {
  const assetsDir = path.join(sourceDir, 'assets');
  if (!fs.existsSync(assetsDir)) return [];
  const copied = [];
  function walk(current, relative) {
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const from = path.join(current, entry.name);
      const rel = path.posix.join(relative, entry.name);
      const to = path.join(outputDir, 'assets', rel);
      if (entry.isDirectory()) {
        fs.mkdirSync(to, { recursive: true });
        walk(from, rel);
      } else if (entry.isFile()) {
        fs.mkdirSync(path.dirname(to), { recursive: true });
        fs.copyFileSync(from, to);
        copied.push(`assets/${rel}`);
      }
    }
  }
  walk(assetsDir, '');
  return copied;
}

export function exportDeck(inputDir, { output, title } = {}) {
  const deck = loadDeck(inputDir);
  const report = validateDeck(deck, { templatesDir: TEMPLATES_DIR });
  if (report.errors.length > 0) {
    const error = new Error(report.errors.join('\n'));
    error.warnings = report.warnings;
    throw error;
  }

  const outputDir = path.resolve(output || defaultOutput(deck.dir));
  fs.mkdirSync(outputDir, { recursive: true });
  const deckTitle = title || deck.metadata.title;
  const compiled = {
    title: deckTitle,
    description: deck.metadata.description || '',
    template: deck.metadata.template,
    aspectRatio: '16:9',
    status: deck.metadata.status || 'draft',
    canonical: deck.metadata.canonical || null,
    slides: deck.slides.map((slide) => ({
      type: slide.type,
      kicker: slide.kicker,
      heading: slide.heading,
      subheading: slide.subheading,
      blocks: slide.blocks,
      media: slide.media,
      notes: slide.notes
    }))
  };

  const templateCssPath = path.join(TEMPLATES_DIR, deck.metadata.template, 'custom.css');
  const templateCss = fs.existsSync(templateCssPath) ? fs.readFileSync(templateCssPath, 'utf8') : '';
  const customCss = `${fs.readFileSync(path.join(VIEWER_DIR, 'deck-base.css'), 'utf8').trim()}\n\n${templateCss.trim()}\n`;
  let html = fs.readFileSync(path.join(VIEWER_DIR, 'index.html'), 'utf8');
  html = replaceOnce(html, '__TITLE__', escapeHtml(deckTitle));
  html = replaceOnce(html, '__TEMPLATE_CLASS__', `template-${deck.metadata.template}`);
  html = replaceOnce(html, '__DECK_JSON__', jsonForScript(compiled));

  fs.writeFileSync(path.join(outputDir, 'index.html'), html);
  fs.copyFileSync(path.join(VIEWER_DIR, 'viewer.css'), path.join(outputDir, 'viewer.css'));
  fs.copyFileSync(path.join(VIEWER_DIR, 'viewer.js'), path.join(outputDir, 'viewer.js'));
  fs.writeFileSync(path.join(outputDir, 'custom.css'), customCss);
  fs.writeFileSync(path.join(outputDir, 'deck.json'), `${JSON.stringify(compiled, null, 2)}\n`);
  fs.copyFileSync(deck.slidesPath, path.join(outputDir, 'slides.md'));
  fs.copyFileSync(deck.metaPath, path.join(outputDir, 'metadata.json'));
  const assets = copyAssets(deck.dir, outputDir);

  const files = [
    'index.html',
    'viewer.css',
    'custom.css',
    'viewer.js',
    'deck.json',
    'slides.md',
    'metadata.json',
    ...assets,
    'export-manifest.json'
  ];
  const manifest = {
    title: deckTitle,
    template: deck.metadata.template,
    source: deck.dir,
    viewer: 'html',
    assets: 'folder',
    slideCount: deck.slides.length,
    status: compiled.status,
    files
  };
  fs.writeFileSync(path.join(outputDir, 'export-manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
  return { outputDir, manifest, warnings: report.warnings };
}

function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help || !options.input) {
    console.log(usage());
    process.exit(options.help ? 0 : 2);
  }
  try {
    const result = exportDeck(options.input, options);
    for (const warning of result.warnings) console.error(`WARNING: ${warning}`);
    console.log(`Wrote ${result.manifest.slideCount} slides to ${result.outputDir}`);
  } catch (error) {
    for (const warning of error.warnings || []) console.error(`WARNING: ${warning}`);
    console.error(`ERROR: ${error.message}`);
    process.exit(1);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
