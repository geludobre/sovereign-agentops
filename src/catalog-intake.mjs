import { createHash } from 'node:crypto';

export const PINNED_SHA = '040a8ea49c773db9e00a946e745d296d3e8dfc75';
const SOURCE = 'https://github.com/cporter202/agentic-ai-apis';
const CANDIDATES = Object.freeze({
  'apify-ai-code-sandbox': 'local Codex/FCC (availability unverified)',
  'apify-ai-web-agent': 'browser/Desktop Commander (availability unverified)',
});
const fail = () => { throw new TypeError('Catalog metadata denied'); };
function exact(value, keys) {
  if (!value || typeof value !== 'object' || Array.isArray(value)
      || Object.keys(value).sort().join(',') !== [...keys].sort().join(',')) fail();
}
const hash = value => createHash('sha256').update(JSON.stringify(value)).digest('hex');

/** Pure, offline discovery projection. Input is curated metadata, never Markdown,
 * commands, upstream code, or authenticated evidence of a Git checkout.
 * No result grants permission to connect, execute, install, or write.
 */
export function importCatalog(input) {
  exact(input, ['sha', 'capturedAt', 'entries']);
  if (input.sha !== PINNED_SHA
      || typeof input.capturedAt !== 'string'
      || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(input.capturedAt)
      || !Number.isFinite(Date.parse(input.capturedAt))
      || new Date(input.capturedAt).toISOString() !== input.capturedAt
      || !Array.isArray(input.entries) || input.entries.length > 2) fail();
  const seen = new Set();
  const entries = input.entries.map(entry => {
    exact(entry, ['id', 'publisherUrl', 'availability', 'permissions', 'action']);
    if (!Object.hasOwn(CANDIDATES, entry.id) || seen.has(entry.id)
        || entry.publisherUrl !== 'https://apify.com'
        || !['unknown', 'unavailable', 'available'].includes(entry.availability)
        || !Array.isArray(entry.permissions) || entry.permissions.length !== 0
        || entry.action !== 'DISCOVERY_ONLY') fail();
    seen.add(entry.id);
    return { id: entry.id, publisherUrl: entry.publisherUrl,
      availability: entry.availability, permissions: [], action: 'DISCOVERY_ONLY' };
  }).sort((a, b) => a.id.localeCompare(b.id));
  const provenance = { source: SOURCE, sha: PINNED_SHA, capturedAt: input.capturedAt,
    issuer: 'local-offline-catalog-intake', verification: 'CALLER_SUPPLIED_UNVERIFIED' };
  const sourceHash = hash({ ...provenance, entries });
  const nodes = entries.map(entry => ({
    ...entry, tag: 'DISCOVERY_ONLY', runtime: 'UNVERIFIED', decision: 'HOLD',
    connectionApproved: false, ...provenance, hash: sourceHash,
    // Scores represent evidence sufficiency (0 = unverified, 1 = local metadata).
    // They are never a runtime trust score or an approval threshold.
    assessment: {
      identity: { score: 0, status: 'UNVERIFIED' },
      publisherProvenance: { score: 0, status: 'UNVERIFIED' },
      license: { score: 0, status: 'RIGHTS_REVIEW_REQUIRED' },
      outboundDestinations: { score: 0, status: 'UNKNOWN' },
      requestedScopes: { score: 0, status: 'RUNTIME_UNKNOWN' },
      secretExposure: { score: 0, status: 'RUNTIME_UNKNOWN_NO_SECRETS_ACCEPTED' },
      executionCost: { score: 0, status: 'UNKNOWN' },
      deterministicReceipts: { score: 1, status: 'LOCAL_METADATA_HASH_ONLY' },
      localReplacement: { score: 0, status: CANDIDATES[entry.id] },
      releaseBlockerValue: { score: 0, status: 'NO_VALIDATED_VALUE' },
    },
  }));
  const graph = { tag: 'DISCOVERY_ONLY', ...provenance, hash: sourceHash, nodes,
    edges: nodes.map(node => ({ from: SOURCE, to: node.id,
      relation: 'DISCOVERY_ONLY', ...provenance, hash: sourceHash,
      runtime: 'UNVERIFIED' })) };
  return { ...graph, receipt: { algorithm: 'sha256', digest: hash(graph), signed: false } };
}
