# Bug report

**Symptom**: `POST /checkout` returns 500 for some users. Server log shows
`ZeroDivisionError: division by zero` coming from the total calculation.

**Reported by**: support ticket #4821

**Repro hint from the reporter**: "it happened right after I emptied my cart
and then applied a coupon that was still in the session."

**Affected code**: `orders.py` (`calculate_total`)

Run the existing tests:

```bash
python -m unittest discover -s tests -v
```
