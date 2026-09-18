import { useState } from 'react';
import { createOrder } from '../api/orders.js';

export function OrderForm({ userId }) {
  const [items, setItems] = useState([]);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit() {
    setSubmitting(true);
    await createOrder(userId, items);
    setSubmitting(false);
  }

  return (
    <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
      <button type="submit" disabled={submitting}>
        Submit order
      </button>
    </form>
  );
}
