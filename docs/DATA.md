# Data contract and provenance

## Included demo
The five CSVs under `data/demo/` are generated from NumPy's seeded random generator (seed 42). They contain fictional numeric IDs, no card numbers, CVV, addresses or names. They are intended for analysis/UI demonstration and regression testing.

Artificial patterns are intentional: a skewed spending distribution, customers with no recent purchases, refunds, error rows and incomplete labels. The probabilities used to generate fraud labels do not describe actual risk.

## Local data
Place these files together in `data/full/`, or select a different local folder:

| File | Required columns |
| --- | --- |
| users_data.csv | id, current_age, yearly_income, total_debt, credit_score |
| cards_data.csv | id, client_id, card_type, card_brand |
| mcc_codes.csv | mcc_code, merchant_category |
| Exactly one transactions_data.csv / transactions_data_25pc.csv / transactions_data_10pc.csv | id, client_id, card_id, date, amount, mcc, use_chip |
| train_fraud_labels.csv (optional) | id, label |

Optional transaction columns: `errors`, `merchant_state`, `merchant_city`.
Extra columns are ignored at ingestion; the application reads an explicit allowlist.

- Primary IDs must be unique nonmissing integers.
- Transaction dates must parse as timezone-naive timestamps; normalize timezone-aware inputs before import.
- Money can be numeric or strings such as `$1,234.50`; missing/nonfinite amounts fail validation.
- Labels accept Yes/No (case insensitive), 1/0, or missing. Unsupported values fail validation.
- Age must be between 0 and 120. Zero/negative income produces unknown debt-to-income.
- The user and card registries should cover every transaction. Unmatched keys are retained and reported.
- A card is joined on both card ID and customer ID. All merges check cardinality to prevent row multiplication.
- Exactly one transaction file is accepted, so samples are not silently substituted or combined.
- Category names and card types should be standardized at source. The credit ownership rule recognizes `Credit`, ignoring case.

All monetary amounts are assumed USD, with the same currency across input tables. The application uses floating-point aggregation for exploratory analytics, not settlement/accounting.

## Original course inputs
The old project referenced external transaction and fraud CSVs but supplied no working download URL or provenance/license information. This revision does not invent either. Old raw user/card CSVs with unnecessary contact/card fields are removed from the current tree; deleting a file does not erase earlier Git history. A local copy can still be analyzed after you verify its source and use rights.

## Cache behavior
The UI cache includes absolute source paths, sizes and nanosecond modification times for every selected file. Replacing or removing a label file changes that key. Reload clears the ingestion cache; derived tables are recalculated on every UI rerun rather than retained in session state.
