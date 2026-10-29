Apply the configured media transfer limit across uploads and downloads together.
Bound upload buffering, report progress only after acknowledgement, and propagate
upload failures instead of returning incomplete uploads as successful. Clean up
cancelled transfers and failed session startup, close streams deterministically,
and remove incomplete downloads on errors. Move file I/O and CDN decryption off
the event loop.
