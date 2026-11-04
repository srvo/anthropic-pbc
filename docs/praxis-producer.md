<!-- praxis-producer-contract:start -->
# Praxis producer integration

Read the [shared producer contract](../../praxis/docs/producer-contract.md) before adding or changing output generation, dataset
registration or custody. The central contract owns the rules; this file is a
portable source pointer, not a second implementation or a runtime acceptance
receipt.

- [Design primitive](../../praxis/design/README.md)
- [Research presentation](../../praxis/design/research-presentation.md)
- [Offline renderer](../../praxis/render/README.md)
- [Semantic lake](../../praxis/docs/semantic-lake.md)
- [Catalog](../../praxis/catalog/README.md)

Reuse central emitters or thin producer adapters. Keep public/private exports,
publication identity, review and signatures separate. Dataset bytes belong to
the one governed lake under verified owner/audience/rights boundaries. Until
actual placement and access/readback receipts exist, preserve authorized local
staging and report the gap; do not claim the transfer completed.

The producer remains responsible for methods, source pins, attribution and
rebuildability. Existing emitters are not automatically rewired, hash pins are
not moved, and data is not uploaded by installing these references. Public
builds do not depend on private coordination plans or a private Dark checkout.
<!-- praxis-producer-contract:end -->
