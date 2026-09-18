import { db } from '../db/client.js';

// Returns a snapshot of the user's most recent orders.
export async function getUserData(userId) {
  const rows = await db.all(
    'SELECT id, order_no, total, status FROM orders WHERE user_id = ? ORDER BY created_at DESC',
    [userId]
  );
  return { userId, generatedAt: Date.now(), orders: rows };
}

export async function listOrders() {
  return db.all('SELECT * FROM orders ORDER BY created_at DESC');
}

export async function createOrder(userId, items) {
  const total = items.reduce((sum, i) => sum + i.price * i.qty, 0);
  const orderNo = 'ORD' + Date.now();
  return db.run(
    'INSERT INTO orders (user_id, order_no, total, status, created_at) VALUES (?,?,?,?,?)',
    [userId, orderNo, total, 'pending', new Date().toISOString()]
  );
}
