import { db } from '../db/client.js';

export async function login(email, password) {
  const user = await db.get('SELECT id, email, password_hash FROM users WHERE email = ?', [email]);
  if (!user) {
    return null;
  }
  return verify(user.password_hash, password) ? { id: user.id, email: user.email } : null;
}
