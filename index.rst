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
The IDF deployment of the alert distribution system uses the `github.com/lsst/idf_deploy`_ for its Terraform configuration.

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
--------------------------

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

1. Log in to Argo (see also :ref:`accessing-argo`).
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

1. Make a change to `github.com/lsst-sqre/phalanx`_'s services/alert-stream-broker/values-idfint.yaml file.
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

1. Delete the user from the list in `github.com/lsst-sqre/phalanx`_'s `services/alert-stream-broker/values-idfint.yaml`_ file.
2. Make a pull request with this change, and make sure it passes automated checks, and get it reviewed.
3. Merge your PR.
4. Delete the user's credentials from 1Password in the RSP-Vault vault of the LSST IT account.
   You can find the credentials by searching by username.
5. Log in to Argo CD.
6. Navigate to the 'alert-stream-broker' application.
7. Click "sync". Click the "prune" checkbox to prune out the defunct user. Apply the sync.

Verify that the user was removed from Kafka by using Kowl and going to the "Access Control List" section (see :ref:`running-kowl`).
The user shouldn't be in the ACLs anymore.

.. _grant_access_to_topic:

Granting users read-only access to a new topic
----------------------------------------------

1. Make a change to `github.com/lsst-sqre/phalanx`_'s `services/alert-stream-broker/values-idfint.yaml`_ file.
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

1. Add a new KafkaTopic resource to the ``templates`` directory in one of the charts that composes the alert-stream-broker service.
   This will be in the `github.com/lsst-sqre/charts`_ repository.
   For example, there is a KafkaTopic resource in the `alert-stream-simulator/templates/kafka-topics.yaml <https://github.com/lsst-sqre/charts/blob/0c2fe6c115623d7ae3852ab63b527a9fcd5d41bf/charts/alert-stream-simulator/templates/kafka-topics.yaml>`__ file.

   These files use the Helm templating language.
   See `The Chart Template Developer's Guide <https://helm.sh/docs/chart_template_guide/>`__ for more information on this language.

   Strimzi's documentation (`"5.2.1: Kafka topic resource" <https://strimzi.io/docs/operators/latest/using.html#ref-operator-topic-str>`__) may be helpful in configuring the topic.
   The schema for KafkaTopic resources has a complete reference at `11.2.90: KafkaTopic schema reference <https://strimzi.io/docs/operators/0.27.1/using.html#type-KafkaTopic-reference>`__.

   Pick the chart that is most relevant to the topic you are adding.
   If it is not relevant to any particular chart, use the general `charts/alert-stream-broker`_ chart.
2. Increment the version of the chart by updating the ``version`` field of its Chart.yaml file.
   For example, `this line <https://github.com/lsst-sqre/charts/blob/0c2fe6c115623d7ae3852ab63b527a9fcd5d41bf/charts/alert-stream-simulator/Chart.yaml#L3>`__ of the alert-stream-simulator chart.
3. Make a pull request with your changes to `github.com/lsst-sqre/charts`_, and make sure it passes automated checks, and get it reviewed.
   Merge your PR.
4. Next, you'll make a change to `github.com/lsst-sqre/phalanx`_ to reference the new chart which has the new KafkaTopic resource.
   Update the `services/alert-stream-broker/Chart.yaml`_ file to reference the new version number of the chart you have updated.
   For example, `this line <https://github.com/lsst-sqre/phalanx/blob/bb417e80e0d9d1148da6edccae400eec006576e1/services/alert-stream-broker/Chart.yaml#L23>`__ would need to be updated if you were adding a topic to the alert-stream-simulator.
5. Make a pull request with your changes to github.com/lsst-sqre/phalanx, and make sure it passes automated checks, and get it reviewd.
   Merge your PR.
6. Wait a few minutes (perhaps 10) for Argo to pick up the change to Phalanx.
7. Log in to Argo CD.
8. Navigate to the 'alert-stream-broker' application.
9. Click 'sync' and leave all the defaults to sync your changes, creating the new topic.

Verify that the change worked by using Kowl and going to the "Topics" section (see :ref:`running-kowl`).
There should be a new topic created.

To let users read from the topic, see :ref:`grant_access_to_topic`.

Granting Alert DB access
------------------------

Alert DB access is governed by membership in GitHub organizations and teams.

The list of permitted GitHub groups for the IDF integration environment is in the `services/gafaelfawr/values-idfint.yaml <https://github.com/lsst-sqre/phalanx/blob/bb417e80e0d9d1148da6edccae400eec006576e1/services/gafaelfawr/values-idfint.yaml#L39-L41>`__ file in github.com/lsst-sqre/phalanx.

As of this writing, that list is composed of 'lsst-sqre-square' and 'lsst-sqre-friends', so any users who wish to have access need to be added to the `"square" <https://github.com/orgs/lsst-sqre/teams/square>`__ or `"friends" <https://github.com/orgs/lsst-sqre/teams/friends>`__ teams in the lsst-sqre GitHub organization.

Invite a user to join one of those groups to grant access.

To change the set of permitted groups, modify the services/gafaelfawr/values-idfint.yaml file to change the list under the ``read:alertdb`` scope.
Then, sync the change to Gafaelfawr via Argo CD.

Making Changes
==============

.. _deploying-a-change:

Deploying a change with Argo
----------------------------

In general, to make any change with ArgoCD, you update Helm charts, update Phalanx, and then "sync" the alert-stream-application:

1. Make desired changes to Helm charts, if required, in `github.com/lsst-sqre/charts`_.
   Note that any changes to Helm charts *always* require the version to be updated.
2. Merge your Helm chart changes.
3. Update the `services/alert-stream-broker/Chart.yaml`_ file to reference the new version number of the chart you have updated, if you made any Helm chart changes.
4. Update the `services/alert-stream-broker/values-idfint.yaml`_ file to pass in any new template parameters, or make modifications to existing ones.
5. Merge your Phalanx changes.
6. Wait a few minutes (perhaps 10) for Argo to pick up the change to Phalanx.
7. Log in to Argo CD at https://data-int.lsst.cloud/argo-cd.
8. Navigate to the 'alert-stream-broker' application.
9. Click 'sync' to synchronize your changes.


Updating the Kafka version
--------------------------

The Kafka version is set in the `alert-stream-broker/templates/kafka.yaml <https://github.com/lsst-sqre/charts/blob/0c2fe6c115623d7ae3852ab63b527a9fcd5d41bf/charts/alert-stream-broker/templates/kafka.yaml#L7>`__ file in `github.com/lsst-sqre/charts`_.
It is parameterized through the ``kafka.version`` value in the alert-stream-broker chart, which defaults to "2.8".

When upgrading the Kafka version, you also may need to update the ``kafka.logMesageFormatVersion`` and ``kafka.interBrokerProtocolVersion``.
These change slowly, but old values can be incompatible with new Kafka versions.
See `Strimzi documentation on Kafka Versions <https://strimzi.io/docs/operators/latest/full/deploying.html#ref-kafka-versions-str>`__ to be sure.

So, to update the version of Kafka used, update the `services/alert-stream-broker/values-idfint.yaml <https://github.com/lsst-sqre/phalanx/blob/master/services/alert-stream-broker/values-idfint.yaml>`__ file in `github.com/lsst-sqre/phalanx`_.
Under ``alert-stream-broker``, then under ``kafka``, add a value: ``version: <whatever you want>``.
If necessary, also set ``logMessageFormatVersion`` and ``interBrokerProtocolVersion`` here.

Then, follow the steps in :ref:`deploying-a-change` to apply these changes.

See also: the Strimzi Documentation's "`9.5: Upgading Kafka <https://strimzi.io/docs/operators/latest/full/deploying.html#assembly-upgrading-kafka-versions-str>`__".

Updating the Strimzi version
----------------------------

First, you probably want to read the Strimzi Documentation's "`9. Upgrading Strimzi <https://strimzi.io/docs/operators/latest/full/deploying.html#assembly-upgrade-str>`__".

The Strimzi version is governed by the version referenced in `github.com/lsst-sqre/phalanx`_'s `services/strimzi/Chart.yaml <https://github.com/lsst-sqre/phalanx/blob/master/services/strimzi/Chart.yaml#L9>`__ file.
Update that version, and do anything else recommended by Strimzi in their documentation, such as changes to resources.

Then, apply the change in a way similar to that described in :ref:`deploying-a-change`.
Note though that you'll be synchronizing the 'strimzi' application in Argo, not the 'alert-stream-broker' application in Argo.

Resizing Kafka broker disk storage
----------------------------------

Some reference reading:

 - DMTN-210's section `3.2.1.3: Storage <https://dmtn-210.lsst.io/#storage>`__.
 - "`Persistent storage improvements <https://strimzi.io/blog/2019/07/08/persistent-storage-improvements/>`__"

Change the alert-stream-broker.kafka.storage.size value in `services/alert-stream-broker/values-idfint.yaml`_ in `github.com/lsst-sqre/phalanx`_.
This is the amount of disk space *per broker instance*.

Apply the change, as described in :ref:`deploying-a-change`.

This may take a little while to apply, since it is handled through the asynchronous Kafka operator, which reconciles storage size every few minutes.
When it starts reconciling, it rolls the change out gradually across the Kafka cluster to maintain availability.

Note that storage sizes can only be increased, never decreased.

Updating the alert schema
-------------------------

For background, you might want to read DMTN-210's section `3.4.4: Schema Synchronization Job <https://dmtn-210.lsst.io/#schema-synchronization-job>`__.

The high-level steps are to:

 - Commit your changes in the lsst/alert_packet repository, obeying its particular versioning system
 - Build a new lsstdm/lsst_alert_packet container
 - Publish a new lsst-alert-packet Python package
 - Load the schema into the schema registry, incrementing the Schema ID
 - Update the alert-stream-simulator to use the new Python package and new schema ID

Making a new alert schema
~~~~~~~~~~~~~~~~~~~~~~~~~

First, make a new subdirectory in `github.com/lsst/alert_packet`_'s `python/lsst/alert/packet/schema <https://github.com/lsst/alert_packet/tree/main/python/lsst/alert/packet/schema>`__ directory.
For example, the current latest version as of this writing is 4.0, so there's a python/lsst/alert/packet/schema/4/0 directory which holds Avro schemas.
You could put a new schema in python/lsst/alert/packet/schema/4/1.

Start by copying the current schema into the new directory, and then make your changes.
Then, update `python/lsst/alert/packet/schema/latest.txt <https://github.com/lsst/alert_packet/blob/main/python/lsst/alert/packet/schema/latest.txt>`__ to reference the new schema version number.

Creating a container which loads the schema
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you are satisfied with your changes, push them and open a PR.
As long as your github branch starts with "tickets/" or is tagged, this will automatically kick off the "`build_sync_container <https://github.com/lsst/alert_packet/blob/main/.github/workflows/build_sync_container.yml>`__" GitHub Actions job, which will create a Docker container holding the alert schema.
The container will be named ``lsstdm/lsst_alert_packet:<tag-or-branch-name>``; slashes are replaced with dashes in the tag-or-branch-name spot.

For example, if you're working on a branch named tickets/DM-34567, then the container will be created and pushed to lsstdm/lsst_alert_packet:tickets-DM-34567.

You can use this ticket-number-based container tag while doing development, but once you're sure of things, merge the PR and then tag a release.
The release tag can be the version of the alert schema (for example "4.1") if you like - it doesn't really matter what value you pick; there are so many version numbers flying around with alert schemas that it's going to be hard to find any scheme which is ideal.

To confirm that your container is working, you can run the conatiner locally.
For example, for the "w.2022.04" tag:

.. code-block:: sh

    -> % docker run --rm lsstdm/lsst_alert_packet:w.2022.04 'syncLatestSchemaToRegistry.py --help'
    usage: syncLatestSchemaToRegistry.py [-h]
                                         [--schema-registry-url SCHEMA_REGISTRY_URL]
                                         [--subject SUBJECT]

    optional arguments:
      -h, --help            show this help message and exit
      --schema-registry-url SCHEMA_REGISTRY_URL
                            URL of a Schema Registry service
      --subject SUBJECT     Schema Registry subject name to use

Loading the new schema into the schema registry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To load the new schema into the schema registry, update the ``alert-stream-schema-registry.schemaSync.image.tag`` value to the tag that you used for the container.

The defaults are set in the alert-stream-schema-registry's `values.yaml <https://github.com/lsst-sqre/charts/blob/7db7ad7cacdf86cc42e5771621162a40f9dc12af/charts/alert-stream-schema-registry/values.yaml#L26-L30>`__ file.
You can update the defaults, or you can update the parameters used in Phalanx for a particular environment under the `alert-stream-schema-registry <https://github.com/lsst-sqre/phalanx/blob/bb417e80e0d9d1148da6edccae400eec006576e1/services/alert-stream-broker/values-idfint.yaml#L75-L77>`__ field.

Apply these changes as described in :ref:`deploying-a-change`.
The result should be that a new schema is added to the schema registry.

Once the change is deployed, the job that loads the schema will start.
You can monitor it in the Argo UI by looking for the Job named 'sync-schema-job'.

You can confirm it worked by using Kowl (see :ref:`running-kowl`) and using its UI for looking at the schema registry's contents.

Publishing a new lsst-alert-packet Python package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The alert stream simulator gets its version of the alert packet schema from the ``lsst-alert-packet`` Python package.
The version of this package that it uses is set in `setup.py <https://github.com/lsst-dm/alert-stream-simulator/blob/main/setup.py#L9>`__ of `github.com/lsst-dm/alert-stream-simulator`_.

You'll need to publish a new version of the lsst-alert-packet Python package in order to get a new version in alert-stream-simulator.

Start by updating the version in `setup.cfg <https://github.com/lsst/alert_packet/blob/main/setup.cfg#L3>`__ of `github.com/lsst/alert_packet`_.
Merge your change which includes the new version in setup.cfg.

The new version of the package needs to be published to PyPI, the Python Package Index: https://pypi.org/project/lsst-alert-packet/.
It is managed by a user named 'lsst-alert-packet-admin', which has credentials stored in 1Password in the RSP-Vault vault.
Use 1Password to get the credentials for that user.

Once you have credentials and have incremented the version, you're ready to publish to PyPI.
Explaining how to do that is out of scope of this guide, but `Twine <https://twine.readthedocs.io/en/stable/>`__ is a good tool for the job.

Updating the Alert Stream Simulator package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The alert stream simulator needs to use the new version of the ``lsst-alert-packet`` version which you published to PyPI.
Second, the chart which runs the simulator needs to be updated to use the right ID of the schema in the schema registry.

The version of ``lsst-alert-packet`` is set in the `setup.py <https://github.com/lsst-dm/alert-stream-simulator/blob/main/setup.py#L9>`__ file of `github.com/lsst-dm/alert-stream-simulator`_.
Update this to include the newly-published Python package.

Once you have made and merged a PR to this, tag a new release of the alert stream simulator using :command:`git tag`.
When your tag has been pushed to the alert stream simulator GitHub repository, an automated build will create a container (in a manner almost exactly the same as you saw for lsst/alert_packet).

You can use :command:`docker run` to verify that this worked.
For example, for version ``v1.2.1``:

.. code-block:: sh

    -> % docker run --rm lsstdm/alert-stream-simulator:v1.2.1 'rubin-alert-sim -h'
    usage: rubin-alert-sim [-h] [-v] [-d]
                           {create-stream,play-stream,print-stream} ...

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         enable info-level logging (default: False)
      -d, --debug           enable debug-level logging (default: False)

    subcommands:
      {create-stream,play-stream,print-stream}
        create-stream       create a stream dataset to be run through the
                            simulation.
        play-stream         play back a stream that has already been created
        print-stream        print the size of messages in the stream in real time



Getting the schema registry's ID
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Next, you'll need to get the ID that is used by the schema registry so that you can use it in the alert stream simulator deployment.
This is easiest to retrieve using Kowl.

Run Kowl (see :ref:`running-kowl`) and then navigate to http://localhost:8080/schema-registry/alert-packet.
There should be a drop-down with different versions. You probably want the latest version, which might already be the one being displayed.
Select the desired version.

At the top of the screen, you should see the "Schema ID" of the schema you have selected.
This integer is an ID we'll need to reference later.

Updating the Alert Stream Simulator values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You're almost done.
We need to update the alert stream simulator deployment to use the new container version, and to use the new schema ID.

The container version is set in `values-idfint.yaml's alert-stream-simulator.image.tag <https://github.com/lsst-sqre/phalanx/blob/bb417e80e0d9d1148da6edccae400eec006576e1/services/alert-stream-broker/values-idfint.yaml#L85>`__ field.
Update this to match the tag you used in github.com/lsst-dm/alert-stream-simulator.

The schema ID is set in values-idfint.yaml as well, under ``alert-stream-simulator.schemaID``.
This is set to ``1`` by default.

Those changes to values-idfint.yaml are half the story.
You probably also should update the defaults, which is done by editing the `values.yaml <https://github.com/lsst-sqre/charts/blob/aa8f4db9a8844d94407b492dac14b56014cecd02/charts/alert-stream-simulator/values.yaml>`__ files in the alert-stream-simulator chart.

Once you have made those changes, apply them following the instructions in :ref:`deploying-a-change`.

The new simulator make take a few minutes to come online as the data needs to be reloaded.
Once the sync has completed, you can verify that the change worked.

Verify that it worked using Kowl (see :ref:`running-kowl`) by looking at the `Messages UI <http://localhost:8080/topics/alerts-simulated?o=-3&p=-1&q&s=50#messages>`__ (keep in mind that it can take up to 37 seconds for messages to appear!).
The mesages should be encoded using your new schema.

.. warning::

   You probably want to change the sample alert data (see :ref:`changing-sample-alert-data`) used by the alert stream simulator.

   If you don't do this, then the alert packets will be decoded using the version used when sample alerts were generated, then *re-encoded* using the new alert schema.

   You can manage this transition using Avro's `aliases <https://avro.apache.org/docs/current/spec.html#Aliases>`__, but it might be simpler to simultaneously switch to a new version of the sample alert data.

.. _changing-sample-alert-data:

Changing the sample alert data
------------------------------

The sample alert data used by the alert stream simulator is set in a Makefile:

.. code-block:: make

    .PHONY: datasets
    datasets: data/rubin_single_ccd_sample.avro data/rubin_single_visit_sample.avro

    data:
            mkdir -p data

    data/rubin_single_ccd_sample.avro: data
            wget --no-verbose --output-document data/rubin_single_ccd_sample.avro https://lsst.ncsa.illinois.edu/~ebellm/sample_precursor_alerts/latest_single_ccd_sample.avro

    data/rubin_single_visit_sample.avro: data
            wget --no-verbose --output-document data/rubin_single_visit_sample.avro https://lsst.ncsa.illinois.edu/~ebellm/sample_precursor_alerts/latest_single_visit_sample.avro

The last two show what's happening.
The sample alerts are downloaded from https://lsst.ncsa.illinois.edu/~ebellm/sample_precursor_alerts/latest_single_visit_sample.avro.

The sample alerts could be retrieved from anywhere else.
The important things are that they should be encoded in Avro Object Container File format (that is, with all alerts in one file, preceded by a single instance of the Avro schema), and that they should represent a single visit of alert packet data.

Make changes to the makefile to get data from somewhere else, and then merge your changes.
Make a git tag using the format ``vX.Y.Z``, for example ``v1.3.10``, and push that git tag up.
This will trigger a build job for the container using the new tag.

Next, copy that tag into `charts/alert-stream-simulator/values.yaml <https://github.com/lsst-sqre/charts/blob/aa8f4db9a8844d94407b492dac14b56014cecd02/charts/alert-stream-simulator/values.yaml#L35>`__, and follow the instructions from :ref:`deploying-a-change`.
This will configure the alert stream simulator to use the new alert data, publishing it every 37 seconds.

Deploying on a new Kubernetes cluster on Google Kubernetes Engine
-----------------------------------------------------------------

Deploying on a new Kubernetes cluster will take a lot of steps, and has not been done before, so this section is somewhat speculative.

Prerequisites
~~~~~~~~~~~~~

There are certain prerequisites before even starting.
These are systems that are dependencies of the alert distribution system's current implementation, so they must be present already.

They are:

 - **Argo CD** should be installed and configured to make deployment possible using configuration from Phalanx and Helm.
   This means there should be some "environment" analogous to "idfint" which is used in the IDF integration deployment.
 - **Gafaelfawr** should be installed to set up the ingress for the alert database.
 - **cert-manager** should be installed so that broker TLS certificates can be automatically provisioned.
 - The **nginx** ingress controller should be installed to set up the ingress for the schema registry.
 - Workload Identity needs to be configured properly (for example, through Terraform) on the Google Kubernetes Engine instance to allow the alert database to gain permissions to interact with Google Cloud Storage buckets.

Preparation with Terraform
~~~~~~~~~~~~~~~~~~~~~~~~~~

Before starting, some resources should be provisioned, presumably using Terraform:

 - A node pool for Kafka instances to run on.
 - Storage buckets for alert packets and schemas.
 - IAM roles providing access to the storage buckets for the alert database ingester and server (as writer and reader, respectively).

The current node pool configuration in the IDFINT environment can be found in the `environments/deployments/science-platform/env/integration-gke.tf <https://github.com/lsst/idf_deploy/blob/main/environment/deployments/science-platform/env/integration-gke.tfvars#L48-L64>`__ file:

.. code-block:: terraform
   :emphasize-lines: 1-17,28-30,36-42

     {
       name = "kafka-pool"
       machine_type = "n2-standard-32"
       node_locations     = "us-central1-b"
       local_ssd_count    = 0
       auto_repair        = true
       auto_upgrade       = true
       preemptible        = false
       image_type         = "cos_containerd"
       enable_secure_boot = true
       disk_size_gb       = "500"
       disk_type          = "pd-standard"
       autoscaling        = true
       initial_node_count = 1
       min_count          = 1
       max_count          = 10
     }
   ]

   node_pools_labels = {
     core-pool = {
       infrastructure = "ok",
       jupyterlab = "ok"
     },
     dask-pool = {
       dask = "ok"
     },
     kafka-pool = {
       kafka = "ok"
     }
   }

   node_pools_taints = {
     core-pool = [],
     dask-pool = []
     kafka-pool = [
       {
         effect = "NO_SCHEDULE"
         key = "kafka",
         value = "ok"
       }
     ]
   }

Storage bucket configuration is in `environment/deployments/science-platform/env/integration-alertdb.tfvars <https://github.com/lsst/idf_deploy/blob/main/environment/deployments/science-platform/env/integration-alertdb.tfvars>`__:

.. code-block:: terraform

    # Project
    environment = "int"
    project_id  = "science-platform-int-dc5d"

    # In integration, only keep 4 weeks of simulated alert data.
    purge_old_alerts  = true
    maximum_alert_age = 28

    writer_k8s_namespace           = "alert-stream-broker"
    writer_k8s_serviceaccount_name = "alert-database-writer"
    reader_k8s_namespace           = "alert-stream-broker"
    reader_k8s_serviceaccount_name = "alert-database-reader"

    # Increase this number to force Terraform to update the int environment.
    # Serial: 2

This references the `environment/deployments/science-platform/alertdb <https://github.com/lsst/idf_deploy/blob/main/environment/deployments/science-platform/alertdb/main.tf>`__ module.

Note that buckets and roles are already created in the RSP's Dev and Prod projects.

It may be helpful to look at the PRs originally configured the Int environment:

 - `#350 Add Kafka node pool to int science platform GKE <https://github.com/lsst/idf_deploy/pull/350>`__
 - `#357 Fix typo in Kafka nodepool declaration <https://github.com/lsst/idf_deploy/pull/357>`__
 - `#371 Add taints to the Kafka node pool on data-int <https://github.com/lsst/idf_deploy/pull/371>`__
 - `#374 Add alert DB backend resources <https://github.com/lsst/idf_deploy/pull/373>`__
 - `#374 Use bucket names which are more likely to be unique <https://github.com/lsst/idf_deploy/pull/374>`__:

Provision the DNS for the schema registry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

DNS is provisioned by the SQuARE team, so you'll have to make requests to them for this part.

The target environment is running Gafaelfawr, so it has some base IP address used for the main ingress.
The schema registry can run on the same IP address, even though it uses a different hostname.

So, request a DNS A record which points to the base IP of the targeted environment's main ingress.

For example, 'data-int.lsst.cloud', which is the base URL for the INT IDF environment, is an A record for '35.238.192.49'.
The schema registry therefore gets a DNS A record 'alert-schemas-int.lsst.cloud' which similarly points to 35.238.192.49.

Configuring a new Phalanx deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You'll need to configure a new Phalanx deployment.

To do this, create a ``values-<environment>.yaml`` file in the `services/alert-stream-broker`_ directory of `github.com/lsst-sqre/phalanx`_ which matches the environment.

You must explicitly set a hostname for the schema registry (in ``alert-stream-schema-registry.hostname`` and ``alert-database.ingester.schemaRegistryURL``).
Use the one you provisioned in the previous step.


You will also need to explicitly pass in the alert database GCP project and bucket names.
Be careful to set the fields of the alert database to the right values that match what you created in Terraform.

Finally, make sure to not set the ``alert-stream-broker.kafka.externalListener`` field yet.
This field uses IPs and hostnames which we don't yet know.

You will similarly need to configure the ``values-<environment>.yaml`` file for Strimzi (in services/strimzi) and for the Strimzi Registry Operator (in services/strimzi_registry_operator).

You will also need to enable the ``alert_stream_broker``, ``strimzi``, and ``strimzi_registry_operator`` applications in the ``science-platform/values-<environment>.yaml`` file.
For example, see the `science-platform/values-idfint.yaml <https://github.com/lsst-sqre/phalanx/blob/master/science-platform/values-idfint.yaml>`__ file, which has ``enabled: true`` for those three apllications.
You need to do that for your target environment as well.

Enabling the new services in Argo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Argo needs to be synced - that is, *the Argo application itself* - in order to detect the newly-enabled ``alert_stream_broker``, ``strimzi``, and ``strimzi_registry_operator`` applications.
Do that first - log in to Argo in the target environment, and sync the Argo application.

Next, sync Strimzi.
It should succeed without errors.

Next, sync the Strimzi Registry Operator.
It should also succeed without errors.

Next, sync the alert stream broker application.
**Errors are expected** at this stage.
Our goal is just to do the initial setup so some of the resources come up, but not everything will work immediately.

Provisioning DNS records
~~~~~~~~~~~~~~~~~~~~~~~~

Once the alert-stream-broker is synced into a half-broken, half-working state, we can start to get the IP addresses used by its services.
This will let us provision more DNS records: those for the Kafka brokers.

To do this, we will use :command:`kubectl` to look up the IP addresses provisioned for the broker (see :ref:`kubectl`).

Run :command:`kubectl get service --namespace alert-stream-broker` to get a list of all the services running:

.. code-block:: sh

    -> % kubectl get service  -n alert-stream-broker
    NAME                                    TYPE           CLUSTER-IP      EXTERNAL-IP      PORT(S)                               AGE
    alert-broker-kafka-0                    LoadBalancer   10.130.20.152   35.239.64.164    9094:31402/TCP                        78d
    alert-broker-kafka-1                    LoadBalancer   10.130.23.65    34.122.165.155   9094:31828/TCP                        78d
    alert-broker-kafka-2                    LoadBalancer   10.130.21.82    35.238.120.127   9094:31070/TCP                        78d
    alert-broker-kafka-bootstrap            ClusterIP      10.130.20.156   <none>           9091/TCP,9092/TCP,9093/TCP            78d
    alert-broker-kafka-brokers              ClusterIP      None            <none>           9090/TCP,9091/TCP,9092/TCP,9093/TCP   78d
    alert-broker-kafka-external-bootstrap   LoadBalancer   10.130.16.127   35.188.169.31    9094:30118/TCP                        78d
    alert-broker-zookeeper-client           ClusterIP      10.130.25.236   <none>           2181/TCP                              78d
    alert-broker-zookeeper-nodes            ClusterIP      None            <none>           2181/TCP,2888/TCP,3888/TCP            78d
    alert-schema-registry                   ClusterIP      10.130.27.137   <none>           8081/TCP                              76d
    alert-stream-broker-alert-database      ClusterIP      10.130.27.41    <none>           3000/TCP                              21d

The important column here is "EXTERNAL-IP."
Use it to discover the IP addresses for each of the individual broker hosts, and for the "external-bootstrap" service.
Request DNS A records that map useful hostnames to these IP addresses - this is done by the SQuARE team, so you'll need help.

Once you have DNS provisioned, make another change to ``values-<environment>.yaml`` to lock in the IP addresses and inform Kafka of the hostnames to use.
For example, here's ``values-idfint.yaml``:

.. code-block::

    alert-stream-broker:
      cluster:
        name: "alert-broker"

      kafka:
        # Addresses based on the state as of 2021-12-02; these were assigned by
        # Google and now we're pinning them.
        externalListener:
          bootstrap:
            ip: 35.188.169.31
            host: alert-stream-int.lsst.cloud
          brokers:
            - ip: 35.239.64.164
              host: alert-stream-int-broker-0.lsst.cloud
            - ip: 34.122.165.155
              host: alert-stream-int-broker-1.lsst.cloud
            - ip: 35.238.120.127
              host: alert-stream-int-broker-2.lsst.cloud

Apply this change as usual (see :ref:`deploying-a-change`).

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


.. _github.com/lsst-sqre/phalanx: https://github.com/lsst-sqre/phalanx
.. _github.com/lsst-sqre/charts: https://github.com/lsst-sqre/charts
.. _github.com/lsst/idf_deploy: https://github.com/lsst/idf_deploy
.. _github.com/lsst/alert_packet: https://github.com/lsst/alert_packet
.. _github.com/lsst-dm/alert-stream-simulator: https://github.com/lsst-dm/alert-stream-simulator
.. _services/alert-stream-broker: https://github.com/lsst-sqre/phalanx/tree/master/services/alert-stream-broker
.. _services/alert-stream-broker/Chart.yaml: https://github.com/lsst-sqre/phalanx/tree/master/services/alert-stream-broker/values-idfint.yaml
.. _services/alert-stream-broker/values-idfint.yaml: https://github.com/lsst-sqre/phalanx/tree/master/services/alert-stream-broker/values-idfint.yaml
.. _charts/alert-stream-broker: https://github.com/lsst-sqre/charts/tree/master/charts/alert-stream-broker>

.. rubric:: References

.. bibliography:: local.bib lsstbib/books.bib lsstbib/lsst.bib lsstbib/lsst-dm.bib lsstbib/refs.bib lsstbib/refs_ads.bib
    :style: lsst_aa
