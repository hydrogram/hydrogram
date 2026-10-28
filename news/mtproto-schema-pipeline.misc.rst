Update the raw MTProto schema from layer 223 to the verified Telegram Desktop
layer 232, with pinned source checksums and a TDLib comparison. Preserve existing
poll, keyboard, and chat-join behavior; correct optional-vector serialization and
track raw support separately from high-level feature coverage. Schema updates now
require reproducible generation and offline tests, and CI publishes actionable
drift reports and validated candidate patches.
