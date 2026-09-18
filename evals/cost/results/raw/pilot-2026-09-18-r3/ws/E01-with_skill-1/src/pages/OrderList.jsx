import theme from '../theme.js';

export function OrderList({ orders }) {
  return (
    <section>
      <h2>Order list</h2>
      {orders.length === 0 ? null : (
        <ul>
          {orders.map((o) => (
            <li key={o.id}>{o.order_no} — {o.total}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
