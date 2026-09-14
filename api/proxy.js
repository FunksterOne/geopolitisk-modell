// /api/proxy.js — Vercel serverless CORS-proxy for Geopolitisk Systemanalyse 2026
//
// Frontend-koden henter RSS-feeder og markedsdata via /api/proxy?url=…
// Kun vertsnavn i ALLOWED slippes gjennom (hindrer at proxyen misbrukes som
// åpen relé). Omdirigeringer (301/302/307/308) følges inntil 3 ganger, men bare
// til tillatte vertsnavn — flere RSS-kilder svarer med redirect til www-/https-varianter.
const https = require('https');
const http  = require('http');

const ALLOWED = [
  'query1.finance.yahoo.com',
  'query2.finance.yahoo.com',
  'stooq.com',
  'rss.nytimes.com',
  'feeds.bbci.co.uk',
  'search.cnbc.com',
  'foreignpolicy.com',
  'geopoliticalfutures.com',
  'www.economist.com',
  'www.aljazeera.com',
  'feeds.content.dowjones.io',
  'rss.politico.com',
  'ix.cnn.io',
  'truthsocial.com',
];

const MAX_REDIRECTS = 3;
const TIMEOUT_MS    = 8000;

function isAllowed(parsed) {
  return (parsed.protocol === 'https:' || parsed.protocol === 'http:') && ALLOWED.includes(parsed.hostname);
}

function fetchUpstream(parsed, res, redirectsLeft, resolve) {
  const client = parsed.protocol === 'https:' ? https : http;
  const options = {
    hostname: parsed.hostname,
    path: parsed.pathname + parsed.search,
    method: 'GET',
    headers: {
      'User-Agent': 'Mozilla/5.0 (compatible; GeopolitiskModell/1.0)',
      'Accept': 'application/json, application/rss+xml, application/atom+xml, text/xml, */*',
      'Accept-Encoding': 'identity',
    },
    timeout: TIMEOUT_MS,
  };

  const proxyReq = client.request(options, (proxyRes) => {
    const status = proxyRes.statusCode || 200;
    const location = proxyRes.headers.location;

    if ([301, 302, 303, 307, 308].includes(status) && location && redirectsLeft > 0) {
      proxyRes.resume(); // tøm strømmen før vi går videre
      let next;
      try { next = new URL(location, parsed); } catch (e) { next = null; }
      if (next && isAllowed(next)) {
        fetchUpstream(next, res, redirectsLeft - 1, resolve);
        return;
      }
      res.status(502).json({ error: 'Omdirigering til ikke-tillatt adresse' });
      resolve();
      return;
    }

    const contentType = proxyRes.headers['content-type'] || 'text/plain';
    res.setHeader('Content-Type', contentType);
    res.setHeader('Cache-Control', 's-maxage=60, stale-while-revalidate=120');
    res.status(status);
    proxyRes.pipe(res);
    proxyRes.on('end', resolve);
  });
  proxyReq.on('error', (err) => { res.status(502).json({ error: err.message }); resolve(); });
  proxyReq.on('timeout', () => { proxyReq.destroy(); res.status(504).json({ error: 'Timeout' }); resolve(); });
  proxyReq.end();
}

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') { res.status(200).end(); return; }

  const target = req.query.url;
  if (!target) { res.status(400).json({ error: 'Mangler ?url= parameter' }); return; }

  let parsed;
  try { parsed = new URL(target); } catch (e) { res.status(400).json({ error: 'Ugyldig URL' }); return; }

  if (!isAllowed(parsed)) {
    res.status(403).json({ error: 'Domene ikke tillatt: ' + parsed.hostname });
    return;
  }

  return new Promise((resolve) => fetchUpstream(parsed, res, MAX_REDIRECTS, resolve));
};
