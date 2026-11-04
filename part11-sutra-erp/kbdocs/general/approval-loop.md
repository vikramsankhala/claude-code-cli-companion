# Purchase orders stuck in approval

## Symptoms

Purchase orders stay in "awaiting approval" indefinitely; approvers say they never received a task.

## Causes

The approval matrix has a gap: no approver covers the order's amount band, or the only approver is the requester, which segregation of duties blocks.

## Resolution

Close the gap in the approval matrix so every amount band has an approver who is not the requester, then re-trigger approval on stuck orders.
