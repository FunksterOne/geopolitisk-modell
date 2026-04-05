// /api/proxy.js — Vercel serverless CORS-proxy for Geopolitisk Systemanalyse 2026
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
  'ix.cnn.io'
  'truthsocial.com',
];

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') { res.status(200).end(); return; }

  const target = req.query.url;
  if (!target) { res.status(400).json({ error: 'Mangler ?url= parameter' }); return; }

  let parsed;
  try { parsed = new URL(target); } catch (e) { res.status(400).json({ error: 'Ugyldig URL' }); return; }

  if (!ALLOWED.includes(parsed.hostname)) {
    res.status(403).json({ error: 'Domene ikke tillatt: ' + parsed.hostname });
    return;
  }

  const client = parsed.protocol === 'https:' ? https : http;
  const options = {
    hostname: parsed.hostname,
    path: parsed.pathname + parsed.search,
    method: 'GET',
    headers: {
      'User-Agent': 'Mozilla/5.0 (compatible; GeopolitiskModell/1.0)',
      'Accept': 'application/json, application/rss+xml, text/xml, */*',
    },
    timeout: 8000,
  };

  return new Promise((resolve) => {
    const proxyReq = client.request(options, (proxyRes) => {
      const contentType = proxyRes.headers['content-type'] || 'text/plain';
      res.setHeader('Content-Type', contentType);
      res.setHeader('Cache-Control', 's-maxage=60, stale-while-revalidate=120');
      res.status(proxyRes.statusCode || 200);
      proxyRes.pipe(res);
      proxyRes.on('end', resolve);
    });
    proxyReq.on('error', (err) => { res.status(502).json({ error: err.message }); resolve(); });
    proxyReq.on('timeout', () => { proxyReq.destroy(); res.status(504).json({ error: 'Timeout' }); resolve(); });
    proxyReq.end();
  });
};
