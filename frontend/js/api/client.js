/**
 * ApiClient: Fetch wrapper for PULSO backend.
 * Used when CONFIG.DATA_SOURCE === "api".
 */
class ApiClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }

  async getState() {
    const res = await fetch(`${this.baseUrl}/api/state`);
    if (!res.ok) throw new Error(`GET /api/state failed: ${res.status}`);
    return res.json();
  }

  async simulate(eventText) {
    const res = await fetch(`${this.baseUrl}/api/simulate`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ event_text: eventText }),
    });
    if (!res.ok) throw new Error(`POST /api/simulate failed: ${res.status}`);
    return res.json();
  }

  async getNews() {
    const res = await fetch(`${this.baseUrl}/api/news`);
    if (!res.ok) throw new Error(`GET /api/news failed: ${res.status}`);
    return res.json();
  }

  async getHealth() {
    const res = await fetch(`${this.baseUrl}/api/health`);
    return res.json();
  }
}
