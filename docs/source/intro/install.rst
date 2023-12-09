Install Guide
=============

Being a modern Python framework, Hydrogram requires an up to date version of Python to be installed in your system.
We recommend using the latest versions of both Python 3 and pip.

-----

Install Hydrogram
-----------------

-   The easiest way to install and upgrade Hydrogram to its latest stable version is by using **pip**:

    .. code-block:: text

        $ pip3 install -U hydrogram

-   or, with :doc:`TgCrypto <../topics/speedups>` as extra requirement (recommended):

    .. code-block:: text

        $ pip3 install -U hydrogram tgcrypto

Bleeding Edge
-------------

You can install the development version from the git ``dev`` branch using this command:

.. code-block:: text

    $ pip3 install -U https://github.com/hydrogram/hydrogram/archive/dev.zip

Verifying
---------

To verify that Hydrogram is correctly installed, open a Python shell and import it.
If no error shows up you are good to go.

.. parsed-literal::

    >>> import hydrogram
    >>> hydrogram.__version__
    'x.y.z'

.. _`Github repo`: http://github.com/hydrogram/hydrogram
