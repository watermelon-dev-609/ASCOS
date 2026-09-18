// Minimal sqlite-shaped client so the sources are readable without a real DB.
export const db = {
  async all(sql, params = []) { return []; },
  async get(sql, params = []) { return null; },
  async run(sql, params = []) { return { changes: 1 }; },
};
