/**
 * Cloudflare Email Worker -> bus-ingress webhook.
 *
 * Deploy on a domain with Email Routing (e.g. bus@yourdomain.com).
 * Every inbound email becomes a generic-JSON POST to /i/email —
 * replaces the IMAP poller entirely when a Cloudflare-routed mailbox
 * is acceptable (no mail bridge, no polling, push instead of pull).
 *
 * wrangler.toml:
 *   name = "bus-email-ingress"
 *   main = "cf-email-worker.js"
 *   compatibility_date = "2025-01-01"
 *   [vars] BUS_INGRESS_URL = "https://ingress.example.com/i/email"
 *   # secrets: wrangler secret put BUS_INGRESS_TOKEN_EMAIL
 *
 * Then bind the address in Cloudflare dashboard:
 *   Email Routing -> Routing rules -> bus@you.com -> Send to Worker.
 */

export default {
  async email(message, env, ctx) {
    const raw = await new Response(message.raw).arrayBuffer();
    const text = new TextDecoder("utf-8", { fatal: false }).decode(raw);

    const body = extractText(text);
    const payload = {
      id: message.headers.get("message-id")?.[0] ||
        `cf-${Date.now()}-${message.from}`,
      from: message.from,
      ts: new Date().toISOString(),
      body,
    };

    const resp = await fetch(env.BUS_INGRESS_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${env.BUS_INGRESS_TOKEN_EMAIL}`,
      },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      // Retry later: fail the delivery so CF re-delivers.
      message.setReject(`bus-ingress ${resp.status}`);
    }
  },
};

/** Minimal MIME extraction: first text/plain part, else raw body. */
function extractText(eml) {
  const sep = eml.indexOf("\r\n\r\n");
  const head = sep >= 0 ? eml.slice(0, sep) : "";
  const rest = sep >= 0 ? eml.slice(sep + 4) : eml;

  const subject =
    /subject:\s*(.+)/i.exec(head)?.[1]?.trim() || "(no subject)";

  const ct = /content-type:\s*([^\s;]+)/i.exec(head)?.[1]?.toLowerCase();
  if (ct && ct.startsWith("multipart/")) {
    const boundary = /boundary="?([^"\s;]+)"?/i.exec(head)?.[1];
    if (boundary) {
      for (const part of rest.split(`--${boundary}`)) {
        if (/content-type:\s*text\/plain/i.test(part)) {
          const p = part.indexOf("\r\n\r\n");
          const txt = p >= 0 ? part.slice(p + 4) : part;
          return `${subject}\n${txt.trim()}`.slice(0, 1900);
        }
      }
    }
  }
  return `${subject}\n${rest.trim()}`.slice(0, 1900);
}
