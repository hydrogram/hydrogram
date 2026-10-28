Use Python 3.11 native timeouts for RPC writes and replies so cancelling an RPC
propagates cancellation and cleans up pending results reliably.
