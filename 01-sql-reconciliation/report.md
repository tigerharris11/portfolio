# Reconciliation report (synthetic data)

## Row counts
| source | row_count | distinct_ids |
|---|---|---|
| ledger | 2000 | 2000 |
| feed | 2010 | 1999 |

## Exceptions found vs. defects injected
| exception_type | records | injected | check |
|---|---|---|---|
| amount_mismatch | 37 | 37 | match |
| date_mismatch | 34 | 34 | match |
| duplicate_in_feed | 11 | 11 | match |
| missing_in_feed | 13 | 13 | match |
| missing_in_ledger | 12 | 12 | match |
| status_mismatch | 41 | 41 | match |

## Largest amount differences
| record_id | ledger_amount | feed_amount | amount_diff |
|---|---|---|---|
| R00337 | 753731.89 | 758638.04 | 4906.15 |
| R01997 | 609899.36 | 614724.36 | 4825.0 |
| R00656 | 302667.21 | 298175.64 | -4491.57 |
| R01043 | 619670.45 | 615444.9 | -4225.55 |
| R01360 | 343008.67 | 346785.47 | 3776.8 |
| R01850 | 245332.85 | 249042.17 | 3709.32 |
| R01262 | 309798.42 | 313446.93 | 3648.51 |
| R01147 | 397698.74 | 401313.73 | 3614.99 |
| R01328 | 554008.87 | 550408.74 | -3600.13 |
| R00548 | 407908.53 | 411431.62 | 3523.09 |
