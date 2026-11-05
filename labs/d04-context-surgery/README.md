# D4 · Context surgery (10 min)

**Feature:** `/context`, `/compact`, `/clear` · **Book:** Part X, Guided Demos; Chapter 4

## Steps

1. Continue the session from D3, or build a long one quickly: ask Claude to read every file in `shopkeeper/` and explain each, then to propose (not write) a data model for discounts by customer tier.
2. Agree a decision, for example: "Tiers are gold 10%, silver 5%; discount applies before GST; store tier on the customer, not the order."
3. Run `/context` and note the largest block (usually messages or tool results).
4. Run:
   ```text
   /compact keep only the decisions about the discount data model
   ```
5. Run `/context` again, then ask: "What did we decide about tiers?"
6. Finish with `/clear` and ask the same question.

## Observe

- After `/compact` the grid shrinks and the tier decision survives.
- After `/clear` it is gone, unless you wrote it down. That is the case for `CLAUDE.md` (Chapter 6): add the decision there and run `/clear` once more.
