# claim_index.json Contract

> **Legacy compatibility only in `claim_pipeline_v1`:** new runs do not emit
> this artifact. Use `claim_pipeline.py write-legacy-claim-index` only when an
> older external consumer explicitly requires it.

`claim_bank.json` is the source of truth for claims. This derived compatibility
index contains only claim text, hash, primary section, source IDs, and metadata.
It does not carry formatter routing state.
