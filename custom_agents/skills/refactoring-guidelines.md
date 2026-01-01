## Refactoring
### Priority sequence (do these in order)

1) **Reduce structural distance first.**  
Move code/data closer to where it’s used—often by moving **behavior to where the data lives**. This may lead to **Value Objects** or **Rich Domain Models**. Align responsibilities with module/class/function boundaries. Prefer **package by feature** (vertical slices) so a feature’s behavior and data live together; avoid layer-based packaging that spreads one feature across the codebase.  
**Exception:** it’s fine to have top-level `application/` and `infrastructure/` (or similar) folders; within them, still prefer packaging by feature.

2) **Let Value Objects emerge from primitive obsession.**  
When you see primitive arguments (strings/ints/etc.) standing in for domain concepts, turn them into **proper objects** that **encapsulate the data** and can **carry behavior**. This often reduces parameters and shared knowledge.
When introducing a new Value Object, first start using it in a single place. But then find and replace other primitives of the same structure and replace it with the Value, too. In the end we expect all such primitives to be encapsulated by this new Value.
Caveat: Ensure the new object attracts behavior. Avoid creating "anemic" wrappers for transient/derived data that simply increase indirection (structural distance).
4) **Then reduce strength (coupling).**  
Prefer smaller APIs, fewer parameters, less shared knowledge. Hide details, encapsulate, and minimize what’s visible externally. If encapsulation requires moves, do them (distance reduction supports strength reduction).

### General rules (apply throughout)

- **Avoid `null`/`None` and defensive coding. Make illegal states unrepresentable.**  
  Don’t make functions handle “maybe missing” arguments. If an input can be absent, model that explicitly (separate function/type, Optional at the boundary, Null Object, or validate/normalize at the edge). Prefer types/invariants that *prevent* invalid states from existing in the first place, so internals operate on **valid, non-null domain values** and logic stays small, direct, and readable.

- **Prefer early returns; avoid `else`.**  
  Handle guards and edge conditions up front with returns/throws. Keep the “happy path” unindented and linear.

- **Name honestly and completely (7 stages of naming).**  
  Use names that state responsibilities, even if long (e.g., `calculate_price_and_ship`) to reveal extraction opportunities. Avoid vague names like `manager`, `service`, `controller`, `context`.

- **Prefer tiny functions.**  
  3 lines is ideal, 5 is acceptable. Keep **one level of indentation per function** whenever possible—extract early to avoid nested control flow.

- **Apply 'Tell, Don't Ask' to avoid Feature Envy.**
  If a method asks an object for data to perform a calculation, move the calculation into that object. Keep logic co-located with the data it operates on to preserve encapsulation and autonomy.
