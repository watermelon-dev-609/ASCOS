# Performance Standard

- Measure before optimizing except obvious pathological cases.
- Watch N+1 queries, unbounded lists, oversized payloads and repeated expensive work.
- Paginate large collections.
- Add caches only with an invalidation strategy and measurable benefit.
- Set timeouts for remote calls.
- Consider backpressure for bursty workloads.
