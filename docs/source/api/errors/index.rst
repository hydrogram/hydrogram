RPC Errors
==========

All Hydrogram API errors live inside the ``errors`` sub-package: ``hydrogram.errors``.
The errors ids listed here are shown as *UPPER_SNAKE_CASE*, but the actual exception names to import from Hydrogram
follow the usual *PascalCase* convention.

.. code-block:: python

    from hydrogram.errors import FloodWait

    try:
        ...
    except FloodWait as e:
        ...

.. hlist::
    :columns: 1

    - :doc:`see-other`
    - :doc:`bad-request`
    - :doc:`unauthorized`
    - :doc:`forbidden`
    - :doc:`not-acceptable`
    - :doc:`flood`
    - :doc:`internal-server-error`

.. toctree::
    :hidden:

    see-other
    bad-request
    unauthorized
    forbidden
    not-acceptable
    flood
    internal-server-error
