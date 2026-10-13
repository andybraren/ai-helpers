import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { parseSlidesMarkdown, validateDeck, loadDeck } from './parse-slides.mjs';
import { exportDeck } from '../../uxd-slides-export/scripts/export-slides.mjs';
import { planGooglePublish } from '../../uxd-slides-publish/scripts/publish-google.mjs';
import { markPublished } from '../../uxd-slides-publish/scripts/mark-published.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const TEMPLATES = path.join(HERE, '..', 'templates');
const VALIDATE = path.join(HERE, 'validate-slides.mjs');
const PUBLISH = path.join(HERE, '..', '..', 'uxd-slides-publish', 'scripts', 'publish-google.mjs');

const SAMPLE = `<!-- type: title -->
# Catalog review

## A decision for the design team

<!-- notes
Open with the decision.
-->

---

<!-- type: content -->
<!-- kicker: Today -->
# One idea

The list hides the **next** step.

- Primary action is below the fold
- Status is easy to miss

---

<!-- type: split -->
<!-- image: assets/screen.svg -->
# Show the screen

Researchers still ask which model they can deploy.

---

<!-- type: quote -->
# A platform engineer

> I can see the names and still not tell what I can deploy.

---

<!-- type: closing -->
# Decide the next check
`;

function writeDeck(root) {
  fs.mkdirSync(path.join(root, 'assets'), { recursive: true });
  fs.writeFileSync(path.join(root, 'assets', 'screen.svg'), '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="40"><rect width="64" height="40" fill="#ee0000"/></svg>');
  fs.writeFileSync(path.join(root, 'slides.md'), SAMPLE);
  fs.writeFileSync(path.join(root, 'metadata.json'), JSON.stringify({
    title: 'Catalog review',
    description: 'Design review for the model catalog list.',
    template: 'design-review',
    aspectRatio: '16:9',
    status: 'draft',
    createdAt: '2026-10-12T12:00:00.000Z',
    updatedAt: '2026-10-12T12:00:00.000Z'
  }, null, 2));
}

test('parses slide types, notes, and a local image', () => {
  const slides = parseSlidesMarkdown(SAMPLE);
  assert.equal(slides.length, 5);
  assert.equal(slides[0].type, 'title');
  assert.equal(slides[0].notes, 'Open with the decision.');
  assert.equal(slides[1].kicker, 'Today');
  assert.equal(slides[1].blocks.find((block) => block.type === 'bullets').items.length, 2);
  assert.equal(slides[2].media.src, 'assets/screen.svg');
  assert.equal(slides[3].blocks[0].type, 'quote');
});

test('rejects a missing asset and accepts a complete deck', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'uxd-slides-'));
  writeDeck(root);
  fs.rmSync(path.join(root, 'assets', 'screen.svg'));
  const broken = loadDeck(root);
  const brokenReport = validateDeck(broken, { templatesDir: TEMPLATES });
  assert.ok(brokenReport.errors.some((error) => error.includes('was not found')));

  writeDeck(root);
  const report = validateDeck(loadDeck(root), { templatesDir: TEMPLATES });
  assert.deepEqual(report.errors, []);
});

test('exports a multi-file viewer and a dry-run does not call Google', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'uxd-slides-'));
  const output = path.join(root, 'export');
  writeDeck(path.join(root, 'slides'));
  const exported = exportDeck(path.join(root, 'slides'), { output });
  for (const file of ['index.html', 'viewer.css', 'custom.css', 'viewer.js', 'deck.json', 'assets/screen.svg']) {
    assert.ok(fs.existsSync(path.join(output, file)), file);
  }
  const html = fs.readFileSync(path.join(output, 'index.html'), 'utf8');
  assert.match(html, /Catalog review/);
  assert.match(html, /href="\.\/custom\.css"/);
  assert.match(html, /src="\.\/viewer\.js"/);
  assert.doesNotMatch(html, /function fit\(/);
  assert.match(fs.readFileSync(path.join(output, 'custom.css'), 'utf8'), /\.slide-title/);
  assert.equal(exported.manifest.slideCount, 5);

  const plan = planGooglePublish(loadDeck(path.join(root, 'slides')), { stamp: 'test' });
  assert.equal(plan.groups.length, 5);
  assert.equal(plan.groups[0][0].createSlide.objectId, 'uxd_test_00');
  assert.equal(plan.imageNotes.length, 1);

  const dry = spawnSync(process.execPath, [PUBLISH, path.join(root, 'slides'), '--dry-run'], { encoding: 'utf8' });
  assert.equal(dry.status, 0, dry.stderr);
  assert.match(dry.stdout, /mode: dry-run/);
  assert.match(dry.stdout, /No Google Slides request was sent/);
  assert.doesNotMatch(dry.stdout, /^url:/m);
});

test('marks a real Google URL and rejects a mismatched one', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'uxd-slides-'));
  writeDeck(root);
  assert.throws(
    () => markPublished(root, { target: 'google-slides', url: 'https://www.figma.com/slides/abc' }),
    /does not look like/
  );
  const metadata = markPublished(root, {
    target: 'google-slides',
    url: 'https://docs.google.com/presentation/d/abc123/edit',
    publishedAt: '2026-10-12T15:00:00.000Z'
  });
  assert.equal(metadata.status, 'published');
  assert.equal(metadata.canonical.target, 'google-slides');
  const exported = exportDeck(root, { output: path.join(root, 'export') });
  const html = fs.readFileSync(path.join(exported.outputDir, 'index.html'), 'utf8');
  assert.match(html, /docs\.google\.com\/presentation\/d\/abc123/);
  assert.match(html, /"status":"published"/);
});

test('template placeholders fail strict validation', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'uxd-slides-'));
  fs.copyFileSync(path.join(TEMPLATES, 'briefing', 'slides.md'), path.join(root, 'slides.md'));
  fs.writeFileSync(path.join(root, 'metadata.json'), JSON.stringify({
    title: 'Placeholder',
    description: 'Template copy',
    template: 'briefing',
    aspectRatio: '16:9',
    status: 'draft',
    createdAt: '2026-10-12T12:00:00.000Z',
    updatedAt: '2026-10-12T12:00:00.000Z'
  }));
  const loose = spawnSync(process.execPath, [VALIDATE, root], { encoding: 'utf8' });
  assert.equal(loose.status, 0, loose.stderr);
  assert.match(loose.stderr, /Replace with/);
  const strict = spawnSync(process.execPath, [VALIDATE, root, '--strict'], { encoding: 'utf8' });
  assert.equal(strict.status, 1);
});
