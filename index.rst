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

Argo CD :cite:`argo-cd-homepage` is a tool for deploying software onto a Kubernetes cluster.
Most changes to the Alert Distribution System are done through Argo.

There's some official `SQuARE-maintained documentation <https://phalanx.lsst.io/service-guide/sync-argo-cd.html>`__ for Argo.
This section tries to summarize what you'd need to know to work with the Alert Distribution System, but that thorough documentation is worth reading too.

.. _accessing-argo:

Accessing Argo
~~~~~~~~~~~~~~

The integration deployment uses the Argo installation at `https://data-int.lsst.cloud/argo-cd <https://data-int.lsst.cloud/argo-cd>`__
Access to that installation is managed by the SQuARE team.

When you go to the Argo UI for the first time, you'll see a big mess of many "applications."
The primary one is named `alert-stream-broker <https://data-int.lsst.cloud/argo-cd/applications/alert-stream-broker>`__, but you may also be interested in the "`strimzi <https://data-int.lsst.cloud/argo-cd/applications/strimzi>`__" and "`strimzi-registry-operator <https://data-int.lsst.cloud/argo-cd/applications/strimzi>`__" ones.

Applying Changes by Syncing
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you're in an application, the main action you take is *syncing*.
When you "sync" an application, you synchronize its state in Kubernetes with a "desired state" which is derived from Git.

You do this by clicking the big "SYNC" button at the top of the Argo UI.
This brings up a daunting list of all the resources that will be synchronized.
Usually you don't want to make changes to the options here, although you might want to enable "prune."

When "prune" is enabled, Argo will delete any orphaned resources that no longer seem to be desired.
Without this option, they will linger around.
They probably won't cause harm, but this can be confusing.

What is "Desired State" in Argo?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The "desired state" of a service is based on whatever is currently in the master branch of the `Phalanx repository`_.
Each application has a matching *service* in the Phalanx repo - for example, `services/alert-stream-broker`_ - which contains a ``Chart.yaml`` file and a ``values-idfint.yaml`` file (and possibly more ``values-*.yaml`` files if the service is deployed to more environments than just the IDF integration environment).

The ``Chart.yaml`` file lists Helm charts - and, very crucially, their versions - that define the actual configuration to be used.
The ``values`` file(s) list the particular configuration values that should be plugged in to the Helm chart templates used by that service.

Most of the sourced Helm charts are found in the `Charts repository`_.
The specific charts used are described in more complete detail in DMTN-210. :cite:`DMTN-210`

Argo is sometimes a little bit delayed from the state of the Phalanx repository, perhaps by a few minutes.
You might want to refresh a few times and make sure that the Git reference listed under "Current Sync Status" on the Argo UI for an application matches what you expect to apply.

.. _Phalanx repository: https://github.com/lsst-sqre/phalanx
.. _Charts repository: https://github.com/lsst-sqre/charts
.. _services/alert-stream-broker: https://github.com/lsst-sqre/phalanx/tree/master/services/alert-stream-broker

1Password
---------

1Password is a password management tool.
LSST IT uses it to distribute passwords, and the SQuARE team has adapted it for managing secrets stored in Kubernetes.

It's worth reading the documentation in Phalanx on this subject:
 - `Add a secret with 1Password and VaultSecret <https://phalanx.lsst.io/service-guide/add-a-onepassword-secret.html>`__
 - `Updating a secret stored in 1Password and VaultSecret <https://phalanx.lsst.io/service-guide/update-a-onepassword-secret.html>`__

Managing the Alert Distribution System requires 1Password access.
The LSST IT team can grant that access.
Then, you'll also need access to the "RSP-Vault" vault in 1Password, which can be granted by the SQuARE team.

The idea is that credentials are stored in a special 1Password vault with carefully formatted fields.
Then you can run the phalanx `installer/update_secrets.sh <https://github.com/lsst-sqre/phalanx/blob/master/installer/update_secrets.sh>`__ script to copy secrets from 1Password into Vault, which is a tool for encrypting secret data.

In the background, a tool called Vault Secrets Operator copies secret data in Vault and puts it into Kubernetes secrets for use in Kubernetes applications.

This is used to manage the passwords for the Kafka users that can access the alert stream: their passwords are set in 1Password, copied into Vault with the script, and then automatically synchronized into Strimzi KafkaUsers (see also: `DMTN-210 3.2.3.1: 1Password, Vault, and Passwords <https://dmtn-210.lsst.io/#password-vault-and-passwords>`__).

Terraform
---------

Terraform is a tool for managing resources stored in Google Cloud through code.
The IDF deployment of the alert distribution system uses the `idf_deploy repository <https://github.com/lsst/idf_deploy>`__ for its Terraform configuration.

That repository hosts documentation directly in its README.
Changes are made entirely through GitHub Actions workflows, so they get applied simply by merging into the main branch.

Google Cloud Console
--------------------

The Google Cloud project which hosts the IDF deployment of the alert distribution system is "science-platform-int".
You can use the Google Cloud Platform's console at https://console.cloud.google.com/home/dashboard?project=science-platform-int-dc5d to see some of the things going on inside the system's cloud resources.

In particular, the `Storage Browser <https://console.cloud.google.com/storage/browser?authuser=3&project=science-platform-int-dc5d>`__ can help with identifying anything going wrong with the storage buckets used by the Alert Database, and the `Kubernetes Engine UIs <https://console.cloud.google.com/kubernetes/workload/overview?authuser=3&project=science-platform-int-dc5d>`__ might help with exploring the behavior of the deployed systems on Kubernetes.


.. _kowl:

Kowl
----

Kowl :cite:`kowl` is a web application that provides a UI for a Kafka broker.
It can help with peeking at messages in the Kafka topics, viewing the broker's configuration, monitoring the state of consumer groups, and more.

Kowl can be run locally using Docker.
It requires superuser permissions in the Kafka broker, which can be first retrieved from 1Password (see :ref:`superuser-creds`).
Then, here's how to run it locally:

.. code-block:: bash

   KAFKA_PASSWORD="..."  # fill this in

   docker run --network=host \
       -p 8080:8080 \
       -e KAFKA_BROKERS=alert-stream-int.lsst.cloud:9094 \
       -e KAFKA_TLS_ENABLED=true \
       -e KAFKA_SASL_ENABLED=true \
       -e KAFKA_SASL_USERNAME="kafka-admin" \
       -e KAFKA_SASL_PASSWORD=$KAFKA_PASSWORD \
       -e KAFKA_SASL_MECHANISM=SCRAM-SHA-512 \
       -e KAFKA_SCHEMAREGISTRY_ENABLED=true \
       -e KAFKA_SCHEMAREGISTRY_URLS=https://alert-schemas-int.lsst.cloud \
       quay.io/cloudhut/kowl:master

Once the Kowl container is running, you can view its UI by going to http://localhost:8080.

You should see something like this:

.. figure:: /_static/kowl_topics.png
   :name: Kowl Topics UI

By clicking on a topic, you can see the deserialized messages in the topic.
You can expand them by clicking the "+" sign in each row next to the "Value" column.
For example:

.. figure:: /_static/kowl_messages.png
   :name: Kowl Messages UI

You can also look at the schema and its versions in the Schema Registry tab:

.. figure:: /_static/kowl_schemas.png
   :name: Kowl Schemas UI

You can use the Consumer Groups tab to see the position of any consumers.
For example, here we can see the Pitt-Google broker:

.. figure:: /_static/kowl_consumers.png
   :name: Kowl Consumer Groups UI

Kowl has many more capabilities.
See the official Kowl documentation :cite:`kowl` for more.

Tool Setup
==========

.. _kubectl:
Getting ``kubectl`` Access
----------------------

1. Install ``kubectl``: https://kubernetes.io/docs/tasks/tools/
2. Install ``gcloud``: https://cloud.google.com/sdk/docs/install
3. Run ":command:`gcloud auth login <your google cloud account>`". For example, ":command:`gcloud auth login swnelson@lsst.cloud`."
4. Run ":command:`gcloud container clusters get-credentials science-platform-int`".

You should now have ``kubectl`` access. Try :command:`kubectl get kafka --namespace alert-stream-broker` to verify. You should see output like this:

.. code-block:: bash

  -> % kubectl get kafka --namespace alert-stream-broker
  NAME           DESIRED KAFKA REPLICAS   DESIRED ZK REPLICAS   READY   WARNINGS
  alert-broker   3                        3                     True

.. _running-kowl:
Running Kowl
------------

0. Make sure you have :command:`docker` installed.
1. Retrieve Kafka superuser credentials, as described in :ref:`superuser-creds`.
2. Run the following:

   .. code-block:: sh

     KAFKA_PASSWORD="..."  # fill this in

     docker run --network=host \
       -p 8080:8080 \
       -e KAFKA_BROKERS=alert-stream-int.lsst.cloud:9094 \
       -e KAFKA_TLS_ENABLED=true \
       -e KAFKA_SASL_ENABLED=true \
       -e KAFKA_SASL_USERNAME="kafka-admin" \
       -e KAFKA_SASL_PASSWORD=$KAFKA_PASSWORD \
       -e KAFKA_SASL_MECHANISM=SCRAM-SHA-512 \
       -e KAFKA_SCHEMAREGISTRY_ENABLED=true \
       -e KAFKA_SCHEMAREGISTRY_URLS=https://alert-schemas-int.lsst.cloud \
       quay.io/cloudhut/kowl:master

3. Go to http://localhost:8080

.. _superuser-creds:
Retrieving Kafka superuser credentials
--------------------------------------

The superuser has access to do anything.
Be careful with these credentials!

The username is "**kafka-admin**".

For the password:

1. Log in to 1Password in the LSST IT account.
2. Go to the "RSP-Vault" vault.
3. Search for "alert-stream idfint kafka-admin".

   You should see something like this:

   .. figure:: /_static/1password_superuser.png

4. Copy the password from the password field.

.. _developer-creds:
Retrieving development credentials
----------------------------------

This user only has limited permissions, mimicking those of a community broker.

The username is "**rubin-communitybroker-idfint**".

For the password:

1. Log in to 1Password in the LSST IT account.
2. Go to the "RSP-Vault" vault.
3. Search for "alert-stream idfint rubin-communitybroker-idfint".

   You should see something like this:

   .. figure:: /_static/1password_devel_user.png

4. Copy the password from the password field.


System Status
=============

.. _connectivity-test:

Testing connectivity
--------------------

First, get the set of developer credentials (:ref:`developer-creds`).

Then, use one of the example consumer applications listed in `sample_alert_info/examples <https://github.com/lsst-dm/sample_alert_info/tree/main/examples/alert_stream_integration_endpoint>`__.
These will show whether you're able to connect to the Kafka stream and receive sample alert packets, as well as whether you're able to retrieve schemas from the Schema Registry.

Checking disk usage
-------------------


First, check how much disk is used by Kafka:

1. Run Kowl, following the instructions in :ref:`running-kowl`.
2. Navigate to the brokers view at http://localhost:8080/brokers.

   You should see the amount of disk used by each broker in the right-most column under "size."

Next, check how much is requested in the persistent volume claims used by the Kafka brokers:

3. Ensure you have :command:`kubectl` access (:ref:`kubectl`).
4. Run :command:`kubectl get pvc --namespace alert-stream-broker`. You should see output like this:

   .. code-block:: sh

      -> % kubectl get pvc -n alert-stream-broker
      NAME                            STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
      data-0-alert-broker-kafka-0     Bound    pvc-e5bf9fb1-e763-4c03-8294-b81a6955bde3   1500Gi     RWO            standard       77d
      data-0-alert-broker-kafka-1     Bound    pvc-c289fc0d-39a0-44b1-b073-2aab5c47ba3a   1500Gi     RWO            standard       77d
      data-0-alert-broker-kafka-2     Bound    pvc-6307f422-0448-45bd-985b-f7e559e54bb9   1500Gi     RWO            standard       77d
      data-alert-broker-zookeeper-0   Bound    pvc-bd8bb38f-a5d3-47f9-a9a1-13c66f04f80e   1000Gi     RWO            standard       77d
      data-alert-broker-zookeeper-1   Bound    pvc-01463914-9b1f-49bd-992f-de0b6b0284ca   1000Gi     RWO            standard       77d
      data-alert-broker-zookeeper-2   Bound    pvc-eb37bbaa-cc49-4541-baf4-6f2444330d6f   1000Gi     RWO            standard       77d



Checking consumer group status
------------------------------

1. Run Kowl, following the instructions in :ref:`running-kowl`.
2. Navigate to the consumer group view at http://localhost:8080/groups

There should be an entry for each consumer group that is connected or has connected recently.

The "Coordinator" column indicates which of the three Kafka broker nodes is used for coordinating the group's partition ownership.

The "Members" column indicates the number of currently-active processes which are consuming data.

The "Lag" column indicates how many messages are unread by the consumer group.

Checking logs
-------------

In general, logs are available on the Google Cloud Log Explorer UI.

To access them:

1. Log in to the Google Cloud console at https://console.cloud.google.com.
2. Navigate to the Log Explorer UI, https://console.cloud.google.com/logs/query
3. Enter a search query. For example:

   .. code-block::

      resource.type="k8s_container"
      resource.labels.container_name="kafka"
      resource.labels.namespace_name="alert-stream-broker"

   This will bring up all logs from Kafka brokers:

   .. figure:: /_static/console_kafka_logs.png


There are additional "Log fields" on the left column.
You can use these to filter to a single one of the three brokers via the "Pod name" field.

You can pick a different time range by clicking on "Last 1 hour" in the top right:

.. figure:: /_static/console_log_timerange.png

See also: the GCP Log Explorer documentation: https://cloud.google.com/logging/docs/view/logs-viewer-interface

Each of the subsections lists search queries that can be used to filter logs.

Checking Kafka logs
~~~~~~~~~~~~~~~~~~~

Search for the following:

.. code-block:: yaml

   resource.type="k8s_container"
   resource.labels.container_name="kafka"
   resource.labels.namespace_name="alert-stream-broker"

Checking Strimzi logs
~~~~~~~~~~~~~~~~~~~~~


Search for the following:

.. code-block:: yaml

   resource.type="k8s_container"
   resource.labels.namespace_name="strimzi"

Checking Strimzi Registry Operator logs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Search for the following:

.. code-block:: yaml

   resource.type="k8s_container"
   resource.labels.namespace_name="strimzi-registry-operator"

Checking Schema Registry logs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Search for the following:

.. code-block:: yaml

   resource.type="k8s_container"
   resource.labels.pod_name:"alert-schema-registry"
   resource.labels.namespace_name="alert-stream-broker"

Checking Alert Database logs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Search for the following:

.. code-block:: yaml

   resource.type="k8s_container"
   resource.labels.pod_name:"alert-database"
   resource.labels.namespace_name="alert-stream-broker"

Checking Alert Stream Simulator logs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Search for the following:

.. code-block:: yaml

   resource.type="k8s_container"
   resource.labels.pod_name="alert-stream-simulator"
   resource.labels.namespace_name="alert-stream-broker"

Administration
==============

Sharing passwords
-----------------

1. Log in to 1Password in the LSST IT account.
2. Go to the "RSP-Vault" vault.
3. Search for the username of the account you want to share.
4. Click on the 3-dot menu in the top right and choose "Share...":

   .. figure:: /_static/1password_sharing.png

   This will open a new browser window for a sharing link.

5. Set the duration and availability as desired, and click "Get Link to Share":

   .. figure:: /_static/1password_sharing_link.png


Share the link as you see fit.

Shared links can also be revoked; see `1Password Documentation <https://support.1password.com/share-items/>`__ for more.


Changing passwords
------------------

1. Log in to 1Password in the LSST IT account.
2. Go to the "RSP-Vault" vault.
3. Search for the username of the account you want to modify.
4. Click on the password field. Generate a new password and set it, and save your changes.
5. Follow the instructions in `Phalanx: Updating a secret stored in 1Password and VaultSecret <https://phalanx.lsst.io/service-guide/update-a-onepassword-secret.html>`__.

Then verify that the change was successful by checking it in Argo.

1. Log in to Argo (see also :ref:`accessing_argo`).
2. Navigate to the "alert-stream-broker" application.
3. In the "filters" on the left side, search for your targeted username in the "Name" field.
   You should see a filtered set of resources now.
4. Click on the "secret" resource and check that it has an "updated" timestamp that is after you made your changes.
   If not, delete the "Secret" resource; it will be automatically recreated quickly.
   Once recreated, the user's password will be updated automatically.

If this seems to be having trouble, consider checking:

 - the Vault Secrets Operator logs to make sure it is updating secrets correctly
 - the Strimzi Entity Operator logs to make sure they are updating user accounts correctly
 - the Kafka broker logs to make sure it's healthy

Adding a new user account
-------------------------

First, generate new credentials for the user:

1. Log in to 1Password in the LSST IT account.
2. Go to the "RSP-Vault" vault.
3. Create a new secret.

   a. Name it "alert-stream idfint <username>".
   b. Set the "Username" field to <username>.
   c. Set the "Password" field to something autogenerated.
   d. Add a field named "generate_secrets_key".
      Set its value to "alert-stream-broker <username>-password"
   e. Add a field named "environment".
      Set its value to "data-int.lsst.cloud"

   If you're running in a different environment than the IDF integration environment, replaced "idfint" and "data-int.lsst.cloud" with appropriate values.
4. Sync the secret into Vault following the instructions in `Phalanx documentation <https://phalanx.lsst.io/service-guide/add-a-onepassword-secret.html#part-3-sync-1password-items-into-vault>`__.

Second, add the user to the configuration for the cluster:

1. Make a change to github.com/lsst-sqre/phalanx's services/alert-stream-broker/values-idfint.yaml file.
   Add the new user to the list of users under ``alert-stream-broker.users``: https://github.com/lsst-sqre/phalanx/blob/bb417e80e0d9d1148da6edccae400eec006576e1/services/alert-stream-broker/values-idfint.yaml#L33-L73

   Make sure you use the same username, and grant it read-only access to the ``alerts-simulated`` topic by setting ``readonlyTopics: ["alerts-simulated"]`` just like the other entries.

   If more topcis should be available, add them.
   If running in a different environment than the IDF integration environment, modify the appropriate config file, not values-idfint.yaml.
2. Make a pull request with your changes, and make sure it passes automated checks, and get it reviewed.
3. Merge your PR. Wait a few minutes (perhaps 10) for Argo to pick up the change.
4. Log in to Argo CD.
5. Navigate to the 'alert-stream-broker' application.
6. Click "sync" and leave all the defaults to sync your changes, creating the new user.

Verify that the new KafkaUser was created by using the filters on the left side to search for the new username.

Verify that the user was added to Kafka by using Kowl and going to the "Access Control List" section (see :ref:`running-kowl`).

Optionally verify that access works using a method similar to that in :ref:`connectivity-test`.

Removing a user account
-----------------------

1. Delete the user from the list in github.com/lsst-sqre/phalanx's services/alert-stream-broker/values-idfint.yaml file.
2. Make a pull request with this change, and make sure it passes automated checks, and get it reviewed.
3. Merge your PR.
4. Delete the user's credentials from 1Password in the RSP-Vault vault of the LSST IT account.
   You can find the credentials by searching by username.
5. Log in to Argo CD.
6. Navigate to the 'alert-stream-broker' application.
7. Click "sync". Click the "prune" checkbox to prune out the defunct user. Apply the sync.

Verify that the user was removed from Kafka by using Kowl and going to the "Access Control List" section (see :ref:`running-kowl`).
The user shouldn't be in the ACLs anymore.

Granting users read-only access to a new topic
----------------------------------------------

1. Make a change to github.com/lsst-sqre/phalanx's services/alert-stream-broker/values-idfint.yaml file.
   In the list of users under ``alert-stream-broker.users``, add the new topic to the ``readonlyTopics`` list for each user that should have access.
2. Make a pull request with your changes, and make sure it passes automated checks, and get it reviewed.
3. Merge your PR. Wait a few minutes (perhaps 10) for Argo to pick up the change.
4. Log in to Argo CD.
5. Navigate to the 'alert-stream-broker' application.
6. Click "sync" and leave all the defaults to sync your changes, modifying access.

Verify that the change worked by using Kowl and going to the "Access Control List" section (see :ref:`running-kowl`).
There should be matching permissions with Resource=TOPIC, Permission=ALLOW, and Principal being the users who were granted access.

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
