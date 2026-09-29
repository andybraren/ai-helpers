#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const VIEWER_DIR = path.join(SCRIPT_DIR, '..', 'viewer');
const VIEWER_HTML = path.join(VIEWER_DIR, 'index.html');
const VIEWER_CSS = path.join(VIEWER_DIR, 'viewer.css');
const VIEWER_JS = path.join(VIEWER_DIR, 'viewer.js');

const MIME_BY_EXTENSION = {
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.webp': 'image/webp',
  '.svg': 'image/svg+xml',
  '.pdf': 'application/pdf'
};

function jsonForScript(value) {
  return JSON.stringify(value)
    .replace(/</g, '\\u003c')
    .replace(/>/g, '\\u003e')
    .replace(/&/g, '\\u0026')
    .replace(/\u2028/g, '\\u2028')
    .replace(/\u2029/g, '\\u2029');
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function readRequired(filePath, label) {
  try {
    return fs.readFileSync(filePath, 'utf8');
  } catch (error) {
    throw new Error(`Could not read ${label} at ${filePath}: ${error.message}`);
  }
}

function replaceOnce(source, token, replacement, label) {
  if (!source.includes(token)) {
    throw new Error(`Viewer ${label} is missing token ${token}.`);
  }
  return source.replace(token, () => replacement);
}

function buildExportHtml(title, canvasData, assetMap, { chrome = 'viewer' } = {}) {
  const html = readRequired(VIEWER_HTML, 'viewer HTML');
  const css = readRequired(VIEWER_CSS, 'viewer CSS');
  const jsTemplate = readRequired(VIEWER_JS, 'viewer JS');
  const bodyClass = chrome === 'none' ? 'no-chrome' : 'viewer-chrome';

  const js = replaceOnce(
    replaceOnce(
      replaceOnce(jsTemplate, '__CANVAS_TITLE__', jsonForScript(title), 'JS'),
      '__CANVAS_DATA__',
      jsonForScript(canvasData),
      'JS'
    ),
    '__ASSET_MAP__',
    jsonForScript(assetMap || {}),
    'JS'
  );

  let bundled = html;
  bundled = replaceOnce(bundled, '__TITLE__', escapeHtml(title), 'HTML');
  bundled = replaceOnce(bundled, '__BODY_CLASS__', bodyClass, 'HTML');
  bundled = replaceOnce(
    bundled,
    '<link rel="stylesheet" href="./viewer.css">',
    `<style>\n${css.trimEnd()}\n</style>`,
    'HTML'
  );
  bundled = replaceOnce(
    bundled,
    '<script src="./viewer.js"></script>',
    `<script>\n${js.trimEnd()}\n</script>`,
    'HTML'
  );
  return bundled;
}

function parseArgs(argv) {
  const options = { chrome: 'viewer', viewer: 'html' };
  const positional = [];
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--output') options.output = argv[++index];
    else if (arg === '--title') options.title = argv[++index];
    else if (arg === '--chrome') options.chrome = argv[++index];
    else if (arg === '--no-chrome') options.chrome = 'none';
    else if (arg === '--viewer') options.viewer = argv[++index];
    else if (arg === '--no-viewer') options.viewer = 'none';
    else if (arg === '--json') options.json = true;
    else if (arg === '--no-json') options.json = false;
    else if (arg === '--assets') options.assets = argv[++index];
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
    'Usage: export-canvas.mjs <canvas-dir|canvas.json> [options]',
    '',
    'Default: a single index.html with the viewer and local assets inlined.',
    '',
    'Options:',
    '  --output <dir>          Output directory (default: sibling export/ when source is canvas/, else <canvas-dir>/export)',
    '  --viewer html|none      Include the interactive HTML viewer (default: html)',
    '  --no-viewer             Alias for --viewer none',
    '  --json                  Also write canvas.json',
    '  --no-json               Omit canvas.json (default when --viewer html)',
    '  --assets inline|folder  Inline local files as data URIs, or copy assets/ (default: inline with HTML, folder without)',
    '  --chrome viewer|none    Show or hide toolbar and status chrome (default: viewer)',
    '  --no-chrome             Alias for --chrome none',
    '  --title <text>          Override metadata or folder title',
    '  -h, --help              Show this help'
  ].join('\n');
}

function readJson(filePath, label) {
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (error) {
    throw new Error(`Could not read ${label} at ${filePath}: ${error.message}`);
  }
}

function resolveExportOptions(options) {
  if (!['html', 'none'].includes(options.viewer)) {
    throw new Error('--viewer must be "html" or "none".');
  }
  if (!['viewer', 'none'].includes(options.chrome)) {
    throw new Error('--chrome must be "viewer" or "none".');
  }

  const includeViewer = options.viewer === 'html';
  const includeJson = options.json ?? !includeViewer;
  const assetsMode = options.assets ?? (includeViewer ? 'inline' : 'folder');

  if (!['inline', 'folder'].includes(assetsMode)) {
    throw new Error('--assets must be "inline" or "folder".');
  }
  if (!includeViewer && !includeJson) {
    throw new Error('Nothing to export: enable --viewer html and/or --json.');
  }

  return { includeViewer, includeJson, assetsMode, chrome: options.chrome };
}

function mimeForFilename(filename) {
  return MIME_BY_EXTENSION[path.extname(filename).toLowerCase()] || 'application/octet-stream';
}

function fileToDataUri(filePath) {
  const bytes = fs.readFileSync(filePath);
  return `data:${mimeForFilename(filePath)};base64,${bytes.toString('base64')}`;
}

function collectLocalAssets(canvasData, folderPath) {
  const assets = [];
  for (const node of canvasData.nodes) {
    if (node.type !== 'file' || typeof node.file !== 'string') continue;
    const match = node.file.match(/(?:^|\/)assets\/([^?#]+)/);
    if (!match) {
      if (!/^(https?:|data:|blob:)/i.test(node.file)) {
        throw new Error(`File node "${node.id || 'unknown'}" must use a portable assets/ path or URL: ${node.file}`);
      }
      continue;
    }
    const filename = match[1];
    const normalized = path.normalize(filename);
    if (path.isAbsolute(normalized) || normalized === '..' || normalized.startsWith(`..${path.sep}`)) {
      throw new Error(`File node "${node.id || 'unknown'}" has an unsafe asset path: ${node.file}`);
    }
    const localPath = path.join(folderPath, 'assets', normalized);
    if (!fs.existsSync(localPath) || !fs.statSync(localPath).isFile()) {
      throw new Error(`File node "${node.id || 'unknown'}" references a missing asset: ${localPath}`);
    }
    assets.push({
      nodeId: node.id || 'unknown',
      file: node.file,
      filename,
      localPath
    });
  }
  return assets;
}

function buildAssetMap(localAssets, assetsMode) {
  const assetMap = {};
  const dataUriByFilename = {};
  for (const asset of localAssets) {
    const mapped = assetsMode === 'inline' ? fileToDataUri(asset.localPath) : asset.filename;
    assetMap[asset.file] = mapped;
    assetMap[asset.filename] = mapped;
    if (assetsMode === 'inline') dataUriByFilename[asset.filename] = mapped;
  }
  return { assetMap, dataUriByFilename };
}

function clearStaleOutputs(outputPath, exportOptions) {
  if (!exportOptions.includeViewer) {
    const htmlPath = path.join(outputPath, 'index.html');
    if (fs.existsSync(htmlPath)) fs.rmSync(htmlPath);
  }
  if (!exportOptions.includeJson) {
    const jsonPath = path.join(outputPath, 'canvas.json');
    if (fs.existsSync(jsonPath)) fs.rmSync(jsonPath);
  }
  if (exportOptions.assetsMode !== 'folder') {
    const assetsPath = path.join(outputPath, 'assets');
    if (fs.existsSync(assetsPath)) fs.rmSync(assetsPath, { recursive: true, force: true });
  }
}

function canvasWithInlineAssets(canvasData, dataUriByFilename) {
  const clone = structuredClone(canvasData);
  for (const node of clone.nodes) {
    if (node.type !== 'file' || typeof node.file !== 'string') continue;
    const match = node.file.match(/(?:^|\/)assets\/([^?#]+)/);
    if (!match) continue;
    const uri = dataUriByFilename[match[1]];
    if (uri) node.file = uri;
  }
  return clone;
}

function defaultOutputPath(folderPath) {
  if (path.basename(folderPath) === 'canvas') {
    return path.join(path.dirname(folderPath), 'export');
  }
  return path.join(folderPath, 'export');
}

function buildViewer(options) {
  if (!options.input) throw new Error('A canvas directory or canvas.json path is required.');
  const exportOptions = resolveExportOptions(options);

  const inputPath = path.resolve(options.input);
  if (!fs.existsSync(inputPath)) throw new Error(`Input does not exist: ${inputPath}`);
  const stats = fs.statSync(inputPath);
  const canvasPath = stats.isDirectory() ? path.join(inputPath, 'canvas.json') : inputPath;
  const folderPath = stats.isDirectory() ? inputPath : path.dirname(inputPath);
  if (path.basename(canvasPath) !== 'canvas.json') throw new Error('Input file must be named canvas.json.');
  if (!fs.existsSync(canvasPath)) throw new Error(`Canvas data not found: ${canvasPath}`);

  const canvasData = readJson(canvasPath, 'canvas JSON');
  if (!Array.isArray(canvasData.nodes) || !Array.isArray(canvasData.edges)) {
    throw new Error('canvas.json must contain nodes and edges arrays.');
  }

  let metadata = {};
  const metadataPath = path.join(folderPath, 'metadata.json');
  if (fs.existsSync(metadataPath)) metadata = readJson(metadataPath, 'metadata JSON');
  const title = options.title || metadata.title || path.basename(folderPath);
  const outputPath = path.resolve(options.output || defaultOutputPath(folderPath));
  if (outputPath === folderPath) throw new Error('Output directory must differ from the canvas source directory.');

  const localAssets = collectLocalAssets(canvasData, folderPath);
  const { assetMap, dataUriByFilename } = buildAssetMap(localAssets, exportOptions.assetsMode);

  fs.mkdirSync(outputPath, { recursive: true });
  clearStaleOutputs(outputPath, exportOptions);
  const written = [];

  if (exportOptions.includeViewer) {
    fs.writeFileSync(
      path.join(outputPath, 'index.html'),
      buildExportHtml(title, canvasData, assetMap, { chrome: exportOptions.chrome })
    );
    written.push('index.html');
  }

  if (exportOptions.includeJson) {
    const jsonData = exportOptions.assetsMode === 'inline'
      ? canvasWithInlineAssets(canvasData, dataUriByFilename)
      : canvasData;
    fs.writeFileSync(path.join(outputPath, 'canvas.json'), `${JSON.stringify(jsonData, null, 2)}\n`);
    written.push('canvas.json');
  }

  if (exportOptions.assetsMode === 'folder') {
    const assetsDir = path.join(folderPath, 'assets');
    if (fs.existsSync(assetsDir)) {
      fs.cpSync(assetsDir, path.join(outputPath, 'assets'), { recursive: true, force: true });
      written.push('assets/');
    }
  }

  const manifest = {
    title,
    id: path.basename(folderPath) === 'canvas' ? path.basename(path.dirname(folderPath)) : path.basename(folderPath),
    viewer: exportOptions.includeViewer ? 'html' : 'none',
    json: exportOptions.includeJson,
    assets: exportOptions.assetsMode,
    chrome: exportOptions.includeViewer ? exportOptions.chrome : null,
    written,
    exportedAt: new Date().toISOString()
  };
  fs.writeFileSync(path.join(outputPath, 'export-manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
  written.push('export-manifest.json');

  return {
    outputPath,
    title,
    chrome: exportOptions.chrome,
    viewer: exportOptions.includeViewer ? 'html' : 'none',
    json: exportOptions.includeJson,
    assets: exportOptions.assetsMode,
    written,
    nodes: canvasData.nodes.length,
    edges: canvasData.edges.length
  };
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    console.log(usage());
    process.exit(0);
  }
  const result = buildViewer(options);
  console.log(`Built "${result.title}" at ${result.outputPath}`);
  console.log(
    `${result.nodes} nodes, ${result.edges} edges, viewer: ${result.viewer}, json: ${result.json ? 'yes' : 'no'}, assets: ${result.assets}, chrome: ${result.chrome}`
  );
  console.log(`Wrote: ${result.written.join(', ') || 'nothing'}`);
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  console.error(usage());
  process.exit(1);
}
