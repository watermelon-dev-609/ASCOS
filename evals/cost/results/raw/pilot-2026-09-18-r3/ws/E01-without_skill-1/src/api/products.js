import { db } from '../db/client.js';

export async function listProducts() {
  return db.all('SELECT id, name, price, stock FROM products');
}

export async function getProduct(id) {
  return db.get('SELECT id, name, price, stock FROM products WHERE id = ?', [id]);
}
