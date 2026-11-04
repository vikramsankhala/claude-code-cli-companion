# Invoice posting fails: tax code missing

## Symptoms

Sales or purchase invoices fail to post with "no tax code for item group"; only items in a new item group are affected.

## Causes

A new item group was created without a tax-code mapping in the country pack, so the tax engine cannot pick a rate.

## Resolution

Map the item group to a tax code in Settings, Compliance, Tax mapping, then repost the failed invoices from the exceptions queue.
