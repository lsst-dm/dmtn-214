..
  Technote content.

:tocdepth: 1

.. Please do not modify tocdepth; will be fixed when a new Sphinx theme is shipped.

.. sectnum::

.. TODO: Delete the note below before merging new content to the main branch.

.. note::

   **This technote is not yet published.**

   This is a practical collection of instructions, troubleshooting tips, and playbooks for managing and maintaining the Alert Distribution System.

.. Add content here.

Basic Tools
===========

ArgoCD
------

Kowl
----

1Password
---------

System Status
=============

Testing connectivity
--------------------

Checking disk usage
-------------------

Checking consumer group status
------------------------------

Checking logs
-------------

Checking Kafka logs
~~~~~~~~~~~~~~~~~~~

Checking Strimzi logs
~~~~~~~~~~~~~~~~~~~~~

Checking Strimzi Registry Operator logs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Checking Schema Registry logs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Checking Alert Database logs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Checking Alert Stream Simulator logs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Administration
==============

Retrieving Kafka superuser credentials
--------------------------------------

Sharing passwords
-----------------

Changing passwords
------------------

Adding a new user account
-------------------------

Removing a user account
-----------------------

Granting users access to a new topic
------------------------------------

Adding a new Kafka topic
------------------------

Granting Alert DB access
------------------------

Making Changes
==============

Deploying a change with Argo
----------------------------

Updating the Kafka version
--------------------------

Updating the Strimzi version
----------------------------

Resizing Kafka broker disk storage
----------------------------------

Updating the alert schema
-------------------------

Changing the sample alert data
------------------------------

Deploying on a new Kubernetes cluster on Google
-----------------------------------------------

Deploying on a new Kubernetes cluster off of Google
---------------------------------------------------

Changing the schema registry hostname
-------------------------------------

Changing the Kafka broker hostnames
-----------------------------------

Changing the alert database URL
-------------------------------

Changing the Kafka hardware
---------------------------

Changing the alert database retention policy
--------------------------------------------

Changing the alert database backing storage buckets
---------------------------------------------------

Troubleshooting
===============

Dealing with a full disk
------------------------

.. rubric:: References

.. bibliography:: local.bib lsstbib/books.bib lsstbib/lsst.bib lsstbib/lsst-dm.bib lsstbib/refs.bib lsstbib/refs_ads.bib
    :style: lsst_aa
