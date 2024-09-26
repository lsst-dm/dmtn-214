..
  Technote content.

:tocdepth: 1

.. sectnum::

.. note::

   This is a practical collection of instructions, troubleshooting tips, and playbooks for managing and maintaining the Alert Distribution System.

This is a collection of instructions for how to operate the Alert Distribution System.
An overview of the system is provided in DMTN-210 :cite:`DMTN-210` which is essential background reading for this document.

Basic Tools
===========

ArgoCD
------

Argo CD :cite:`argo-cd-homepage` is a tool for deploying software onto a Kubernetes cluster.
Most changes to the Alert Distribution System are done through Argo.

There's some official `SQuARE-maintained documentation <https://phalanx.lsst.io/applications/argocd/index.html#std-px-app-argocd>`__ for Argo.
This section tries to summarize what you'd need to know to work with the Alert Distribution System, but that thorough documentation is worth reading too.

.. _accessing-argo:

Accessing Argo
~~~~~~~~~~~~~~

To access the Alert Stream Broker deployment at the USDF, use the Argo installation at
`https://k8s.slac.stanford.edu/usdf-alert-stream-broker-dev/argo-cd/applications <https://k8s.slac.stanford.edu/usdf-alert-stream-broker-dev/argo-cd/applications>`__.
Access to that installation is managed by the SQuARE team.

When you go to the Argo UI for the first time, you'll see a big mess of many "applications."
The primary one is named `alert-stream-broker <https://k8s.slac.stanford.edu/usdf-alert-stream-broker-dev/argo-cd/applications/argocd/alert-stream-broker?view=tree>`__, but you may also be interested in the "`strimzi <https://data-int.lsst.cloud/argo-cd/applications/strimzi>`__" and "`strimzi-registry-operator <https://data-int.lsst.cloud/argo-cd/applications/strimzi>`__" ones.

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

Additionally, some resources may not update properly if they
depend on updates in other applications. These may require you to delete that specific resources and then re-deploy.

The recommended deployment order for easy troubleshooting is:

1. Deploy the controller nodepool.
2. Deploy the kafka nodepool. Note: Both will be empty until Kafka is deployed
3. Deploy Alert Stream Kafka. Note: It may take some time for the deployment to create the services and pods
4. Deploy strimzi registry operator
5. Deploy the schema registry
6. Deploy the ingress schema for the schema registry
7. Deploy other services

The strimzi registry operator and schema registry can be a bit of a chicken or egg problem, and you
may have to re-deploy the operator again after the schema registry, and then redeploy the registry for
the two to reconcile with each other after the schema ingress and schema registry are deployed. If Kafka has not
properly built and all pods have not properly built, you will likely end up wih and empty schema registry.

Troubleshooting
~~~~~~~~~~~~~~~

If all of the brokers have failed but everything else is running, the brokers may be out of storage.
This means that Kafka needs to have either the storage allotted or the retention limits adjusted. This requires a restart
of the brokers, and may require a full re-deployment of the whole system.

If you are fully restarting the Alert Broker, you may need to comment out the external load balancer and broker IP's.
Comment out all of the code starting from the lines pictured below through the rest of the code block. This needs
to be done in both `kafka.yaml`_ and `values-usdfdev-alert-stream-broker.yaml`_. Once the pods are up and running, uncomment the code so that
the external bootstrap starts up and the IP's are properly assigned to the pods.

.. figure:: /_static/kafka_yaml.png
   :name: Kafka Yaml

.. figure:: /_static/values_yaml.png
   :name: Values Yaml

If you try and restart the brokers from a fail state (whether they have run out of storage or not), and they end up in crashback loops,
make sure to delete their persistent volume claims to ensure that they can rebuild.

If, during deployment, any resource begins to error continuously, you can delete that specific resource while troubleshooting.
This prevents the status channel from being continuously spammed with errors.
It is recommended to grab the error log first from the logs tab first before deleting the resources.

If you are attempting to delete the topics and they are stuck deleting, you need to remove the finalizers from the topics
to allow them to be deleted. This is done via the following command.

 .. code-block:: bash

     kubectl patch kafkatopics.kafka.strimzi.io TOPIC-NAME --namespace alert-stream-broker -p '{"metadata":{"finalizers": []}}' --type=merge

Replace TOPIC-NAME with the stuck topics.

If for some reason the instance of alert-stream-broker has been removed from the active applications, you can re-deploy it by going to the
`usdf-alert-stream-broker-dev`_ application and re-syncing alert-stream-broker.

If the alert-stream-broker-sync-schema job is failing, this may be related to several issues. If the alert-stream-broker
application has been completely rebuilt from scratch, then the schema registry may not be fully set up. Check that the
schema registry looks like this:

.. figure:: /_static/argocd_schema_registry.png
   :name: Fully Deployed Schema Registry

If it does not, follow the steps listed above. The sync schema job will still fail after this, as the alert-schema-registry
application currently defaults to forward compatibility. This will need to be changed to none.

.. figure:: /_static/argocd_deployed_registry.png
   :name: Deployed Schema Registry

.. figure:: /_static/argocd_schema_compatibility.png
   :name: Schema Compatibility Level

If you receive any errors that a service already exists or resources are being used by an existing service, and you cannot
see that service or resource from argocd or kubectl, then the service or resource may not be accessible. The service/resource
may still exist but needs to be manually deleted by a kubernetes administrator.

Additionally, if resources or services are stuck or not deploying and there are no errors or the services does not produce
a log, you can check the strimzi operator pod within the strimzi application in argo. There may be additional log
information there.


What is "Desired State" in Argo?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The "desired state" of a service is based on whatever is currently in the master branch of the `Phalanx repository`_.
Each application has a matching *service* in the Phalanx repo - for example, `applications/alert-stream-broker`_ - which contains a ``Chart.yaml`` file,
a charts directory containing several charts the broker depends on, and a ``values-usdfdev-alert-stream-broker.yaml`` file (and possibly more ``values-*.yaml`` files if the service is deployed to more environments than just the  integration environment).

The ``Chart.yaml`` file lists Helm charts - and, very crucially, their versions - that define the actual configuration to be used.
The ``values-`` file(s) list the particular configuration values that should be plugged in to the Helm chart templates used by that service in that
specific environment.
The ``values.yaml`` file should only contain information that is agnostic to which environment the service is in.

Most of the sourced Helm charts are found in the `Charts directory of alert-stream-broker`_.
The specific charts used are described in more complete detail in DMTN-210. :cite:`DMTN-210`

Argo is sometimes a little bit delayed from the state of the Phalanx repository, perhaps by a few minutes.
You might want to refresh a few times and make sure that the Git reference listed under "Current Sync Status" on the Argo UI for an application matches what you expect to apply.

.. _Phalanx repository: https://github.com/lsst-sqre/phalanx
.. _Charts directory of alert-stream-broker: https://github.com/lsst-sqre/phalanx/tree/main/applications/alert-stream-broker/charts

For troubleshooting: Changes to the strimzi-operator may cause the alert-schema-registry to not fully deploy.



1Password
---------

1Password is a password management tool.
LSST IT uses it to distribute passwords, and the SQuARE team has adapted it for managing secrets stored in Kubernetes.

It's worth reading the documentation in Phalanx on this subject:
 - `Add a secret with 1Password and VaultSecret <https://phalanx.lsst.io/developers/add-a-onepassword-secret.html>`__
 - `Updating a secret stored in 1Password and VaultSecret <https://phalanx.lsst.io/developers/update-a-onepassword-secret.html>`__

Managing the Alert Distribution System requires 1Password access.
The LSST IT team can grant that access.
Then, you'll also need access to the "RSP-Vault" vault in 1Password, which can be granted by the SQuARE team.

The idea is that credentials are stored in a special 1Password vault with carefully formatted fields.
Then you can run the phalanx `installer/update_secrets.sh <https://github.com/lsst-sqre/phalanx/blob/master/installer/update_secrets.sh>`__ script to copy secrets from 1Password into Vault, which is a tool for encrypting secret data.

In the background, a tool called Vault Secrets Operator copies secret data in Vault and puts it into Kubernetes secrets for use in Kubernetes applications.

This is used to manage the passwords for the Kafka users that can access the alert stream: their passwords are set in 1Password, copied into Vault with the script, and then automatically synchronized into Strimzi KafkaUsers (see also: `DMTN-210 3.2.3.1: 1Password, Vault, and Passwords <https://dmtn-210.lsst.io/#password-vault-and-passwords>`__).

.. _kowl:

Kowl
----

Kowl :cite:`kowl` is a web application that provides a UI for a Kafka broker.
It can help with peeking at messages in the Kafka topics, viewing the broker's configuration, monitoring the state of consumer groups, and more.

Kowl can be run locally using Docker.
It requires superuser permissions in the Kafka broker, which can be first retrieved from 1Password (see :ref:`superuser-creds`). The
credentials for the USDF are currently labeled with `idfint` and will be updated in the future.
Then, start up Docker and enter the following:

.. code-block:: bash

   export KAFKA_USER=$(op item get "alert-stream idfint kafka-admin" --fields label=username)
   export KAFKA_PASSWORD=$(op item get "alert-stream idfint kafka-admin" --fields label=password)

   docker run \
       -p 8080:8080 \
       -e KAFKA_BROKERS=usdf-alert-stream-dev-broker-0.lsst.cloud:9094 \
       -e KAFKA_TLS_ENABLED=false \
       -e KAFKA_SASL_ENABLED=true \
       -e KAFKA_SASL_USERNAME=$KAFKA_USER \
       -e KAFKA_SASL_PASSWORD=$KAFKA_PASSWORD \
       -e KAFKA_SASL_MECHANISM=SCRAM-SHA-512 \
       -e KAFKA_SCHEMAREGISTRY_ENABLED=true \
       -e KAFKA_SCHEMAREGISTRY_URLS=https:///usdf-alert-schemas-dev.slac.stanford.edu \
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

Note: Do not use --network=host, as the current behavior doesn't allow docker to publish
port 8080 and you won't be able to access the Kowl through the local host.

Tool Setup
==========

.. _kubectl:

Getting ``kubectl`` Access for USDF
--------------------------------------

1. Install ``kubectl``: https://kubernetes.io/docs/tasks/tools/
2. Go to https://k8s.slac.stanford.edu/usdf-alert-stream-broker-dev and login using your SLAC credentials.
3. Follow the instructions to gain set up kubectl.

You should now have ``kubectl`` access. Try :command:`kubectl get kafka --namespace alert-stream-broker` to verify. You should see output like this:

.. code-block:: bash

  -> % kubectl get kafka --namespace alert-stream-broker
  NAME           DESIRED KAFKA REPLICAS   DESIRED ZK REPLICAS   READY   WARNINGS
  alert-broker   6                        3                     True    True

.. _running-kowl:

Secure Password Use
-------------------

In the following sections, you CAN fill in both the username and the password manually on your command line. However, this
is not secure and can leave the password/usernames in your command line history. Instead, if you are using 1password, you
should use `1passwords command line tool  <https://1password.com/downloads/command-line/>`__ so that you do not directly enter your credentials.

Running Kowl
------------

0. Make sure you have :command:`docker` installed.
1. Make sure the Docker daemon is running. If using Docker Desktop start up the application.
2. Retrieve Kafka superuser credentials, as described in :ref:`superuser-creds`.
3. Run the following:

   .. code-block:: sh

     export KAFKA_USER=$(op item get "alert-stream idfint kafka-admin" --fields label=username)
     export KAFKA_PASSWORD=$(op item get "alert-stream idfint kafka-admin" --fields label=password)

     docker run \
       -p 8080:8080 \
       -e KAFKA_BROKERS=usdf-alert-stream-dev-broker-0.lsst.cloud:9094 \
       -e KAFKA_TLS_ENABLED=false \
       -e KAFKA_SASL_ENABLED=true \
       -e KAFKA_SASL_USERNAME=$KAFKA_USER \
       -e KAFKA_SASL_PASSWORD=$KAFKA_PASSWORD \
       -e KAFKA_SASL_MECHANISM=SCRAM-SHA-512 \
       -e KAFKA_SCHEMAREGISTRY_ENABLED=true \
       -e KAFKA_SCHEMAREGISTRY_URLS=https:///usdf-alert-schemas-dev.slac.stanford.edu \
       quay.io/cloudhut/kowl:master

3. Go to http://localhost:8080

.. _superuser-creds:

Retrieving Kafka superuser credentials
--------------------------------------

The superuser has access to do anything.
Be careful with these credentials! To find
the credentials:

1. Log in to 1Password in the LSST IT account.
2. Go to the "RSP-Vault" vault.
3. Search for "alert-stream idfint kafka-admin".

.. _developer-creds:

Retrieving development credentials
----------------------------------

This user only has limited permissions, mimicking those of a community broker.

1. Log in to 1Password in the LSST IT account.
2. Go to the "RSP-Vault" vault.
3. Search for "alert-stream idfint rubin-communitybroker-idfint".

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
        NAME                               STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS        VOLUMEATTRIBUTESCLASS   AGE
        data-0-alert-broker-controller-0   Bound    pvc-7ec41769-3643-40ef-8bcb-0aa0f377e093   20Gi       RWO            wekafs--sdf-k8s01   <unset>                 22h
        data-0-alert-broker-controller-1   Bound    pvc-a3102c54-2bb5-4f68-b4d0-921cce2cd57a   20Gi       RWO            wekafs--sdf-k8s01   <unset>                 22h
        data-0-alert-broker-controller-2   Bound    pvc-9c85d80c-b5a6-4d81-a95d-c2b734e9429e   20Gi       RWO            wekafs--sdf-k8s01   <unset>                 22h
        data-0-alert-broker-controller-3   Bound    pvc-3aa61263-dd82-4890-8bab-b038b154a845   20Gi       RWO            wekafs--sdf-k8s01   <unset>                 22h
        data-0-alert-broker-controller-4   Bound    pvc-f42e1031-903d-4923-8c6f-b4b91f6e6a0b   20Gi       RWO            wekafs--sdf-k8s01   <unset>                 22h
        data-0-alert-broker-controller-5   Bound    pvc-737b03a7-144e-4371-9c98-352870afe070   20Gi       RWO            wekafs--sdf-k8s01   <unset>                 22h
        data-0-alert-broker-kafka-10       Bound    pvc-ce20e21b-4e04-419f-bf03-fea6b0ff10ca   2500Gi     RWO            wekafs--sdf-k8s01   <unset>                 22h
        data-0-alert-broker-kafka-11       Bound    pvc-e52f5109-7fac-4a37-a505-2f0c624696e4   2500Gi     RWO            wekafs--sdf-k8s01   <unset>                 22h
        data-0-alert-broker-kafka-6        Bound    pvc-7b59f3ad-e6d3-4063-87ae-b2b2732c93af   2500Gi     RWO            wekafs--sdf-k8s01   <unset>                 22h
        data-0-alert-broker-kafka-7        Bound    pvc-1d9bdef8-e524-41ad-8cf0-12db3c9ea101   2500Gi     RWO            wekafs--sdf-k8s01   <unset>                 22h
        data-0-alert-broker-kafka-8        Bound    pvc-be557069-a4bb-4def-abf1-5a386535b616   2500Gi     RWO            wekafs--sdf-k8s01   <unset>                 22h
        data-0-alert-broker-kafka-9        Bound    pvc-218f52f6-b7b2-4948-97cc-2792fd1e8dfb   2500Gi     RWO            wekafs--sdf-k8s01   <unset>                 22h


Checking consumer group status
------------------------------

1. Run Kowl, following the instructions in :ref:`running-kowl`.
2. Navigate to the consumer group view at http://localhost:8080/groups

There should be an entry for each consumer group that is connected or has connected recently.

The "Coordinator" column indicates which of the three Kafka broker nodes is used for coordinating the group's partition ownership.

The "Members" column indicates the number of currently-active processes which are consuming data.

The "Lag" column indicates how many messages are unread by the consumer group.


Checking logs on Argo
---------------------
Logs are also available in Argo. To look at the logs, pick the specific tile you would like to view and click LOGS. These
can be viewed in the browser or downloaded. Tiles which have logs are Pods, Deployments, Jobs, and ReplicaSets.

In the browser, you can view the logs from the previous container restarts. You can also use keywords such as `DEBUG` or `ERROR` to search for specific
messages within the logs via the search bar.

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
5. Follow the instructions in `Phalanx: Updating a secret stored in 1Password and VaultSecret <https://phalanx.lsst.io/developers/update-a-onepassword-secret.html>`__.

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

.. _new-user:

Adding a new user account
-------------------------

First, generate new credentials for the user:

1. Log in to 1Password in the LSST IT account.
2. Go to the "RSP-Vault" vault.
3. Create a new secret.

   a. Name it "alert-stream usdf <username>".
   b. Set the "Username" field to <username>.
   c. Set the "Password" field to something autogenerated.
   d. Add a field named "generate_secrets_key".
      Set its value to "alert-stream-broker <username>-password"
   e. Add a field named "environment".
      Set its value to "data-int.lsst.cloud"

   If you're running in a different environment than the USDF integration environment, replaced "usdf" and "data-int.lsst.cloud" with appropriate values.
4. Sync the secret into Vault following the instructions in `Phalanx documentation <https://phalanx.lsst.io/developers/update-a-onepassword-secret.html>`__.

Second, add the user to the configuration for the cluster:

1. Make a change to `github.com/lsst-sqre/phalanx`_'s applications/alert-stream-broker/values-usdfdev-alert-stream-broker.yaml
 file.
   Add the new user to the list of users under ``alert-stream-broker.users``: https://github.com/lsst-sqre/phalanx/blob/4f65bb054229d0fd95ee95b50a18a124611411e6/applications/alert-stream-broker/values-usdfdev-alert-stream-broker.yaml#L71C1-L71C1

   Make sure you use the same username, and grant it read-only access to the ``alerts-simulated`` topic by setting ``readonlyTopics: ["alerts-simulated"]`` just like the other entries.

   If more topics should be available, add them.
   If running in a different environment than the USDF integration environment, modify the appropriate config file, not values-usdfdev-alert-stream-broker.yaml.
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

1. Delete the user from the list in `github.com/lsst-sqre/phalanx`_'s `applications/alert-stream-broker/values-usdfdev-alert-stream-broker.yaml`_ file.
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

1. Make a change to `github.com/lsst-sqre/phalanx`_'s `applications/alert-stream-broker/values-usdfdev-alert-stream-broker.yaml`_ file.
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
   This will be in the `alert-stream-broker/charts`_ repository.
   For example, there is a KafkaTopic resource in the `alert-stream-simulator/templates/kafka-topics.yaml <https://github.com/lsst-sqre/phalanx/blob/main/applications/alert-stream-broker/charts/alert-stream-simulator/templates/kafka-topics.yaml>`__ file.

   These files use the Helm templating language.
   See `The Chart Template Developer's Guide <https://helm.sh/docs/chart_template_guide/>`__ for more information on this language.

   Strimzi's documentation (`"5.2.1: Kafka topic resource" <https://strimzi.io/docs/operators/latest/using.html#ref-operator-topic-str>`__) may be helpful in configuring the topic.
   The schema for KafkaTopic resources has a complete reference at `11.2.90: KafkaTopic schema reference <https://strimzi.io/docs/operators/0.27.1/using.html#type-KafkaTopic-reference>`__.

   Pick the chart that is most relevant to the topic you are adding.
   If it is not relevant to any particular chart, use the general `charts/alert-stream-broker`_ chart.
2. Increment the version of the chart by updating the ``version`` field of its Chart.yaml file.
   For example, `this line <https://github.com/lsst-sqre/charts/blob/0c2fe6c115623d7ae3852ab63b527a9fcd5d41bf/charts/alert-stream-simulator/Chart.yaml#L3>`__ of the alert-stream-simulator chart.
3. Make a pull request with your changes to `alert-stream-broker/charts`_, and make sure it passes automated checks, and get it reviewed.
   Merge your PR.
4. Next, you'll update the `applications/alert-stream-broker/Chart.yaml`_ file to reference the new version number of the chart you have updated.
   For example, `this line <https://github.com/lsst-sqre/phalanx/blob/4f65bb054229d0fd95ee95b50a18a124611411e6/applications/alert-stream-broker/charts/alert-stream-broker/Chart.yaml#L3>`__ would need to be updated if you were adding a topic to the alert-stream-simulator.
5. Make a pull request with your changes to github.com/lsst-sqre/phalanx, and make sure it passes automated checks, and get it reviewed.
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

The list of permitted GitHub groups for the USDF integration environment is in the `applications/gafaelfawr/values-idfint.yaml <https://github.com/lsst-sqre/phalanx/blob/bb417e80e0d9d1148da6edccae400eec006576e1/services/gafaelfawr/values-idfint.yaml#L39-L41>`__ file in github.com/lsst-sqre/phalanx.

As of this writing, that list is composed of 'lsst-sqre-square' and 'lsst-sqre-friends', so any users who wish to have access need to be added to the `"square" <https://github.com/orgs/lsst-sqre/teams/square>`__ or `"friends" <https://github.com/orgs/lsst-sqre/teams/friends>`__ teams in the lsst-sqre GitHub organization.

Invite a user to join one of those groups to grant access.

To change the set of permitted groups, modify the applications/gafaelfawr/values-idfint.yaml file to change the list under the ``read:alertdb`` scope.
Then, sync the change to Gafaelfawr via Argo CD.

Making Changes
==============

.. _deploying-a-change:

Deploying a change with Argo
----------------------------

In general, to make any change with ArgoCD, you update Helm charts, update Phalanx, and then "sync" the alert-stream-application:

1. Make desired changes to Helm charts, if required, in `alert-stream-broker/charts`_.
   Note that any changes to Helm charts *always* require the version to be updated.
2. Merge your Helm chart changes.
3. Update the `applications/alert-stream-broker/Chart.yaml`_ file to reference the new version number of the chart you have updated, if you made any Helm chart changes.
4. Update the `applications/alert-stream-broker/values-usdfdev-alert-stream-broker.yaml`_ file to pass in any new template parameters, or make modifications to existing ones.
5. Merge your Phalanx changes.
6. Wait a few minutes (perhaps 10) for Argo to pick up the change to Phalanx.
7. Log in to Argo CD at https://k8s.slac.stanford.edu/usdf-alert-stream-broker-dev/argo-cd.
8. Navigate to the 'alert-stream-broker' application.
9. Click 'sync' to synchronize your changes.


Updating the Kafka version
--------------------------

The Kafka version is set in the `alert-stream-broker/templates/kafka.yaml <https://github.com/lsst-sqre/phalanx/blob/main/applications/alert-stream-broker/charts/alert-stream-broker/templates/kafka.yaml>`__ file in `applications/alert-stream-broker`_.
It is parameterized through the ``kafka.version`` value in the alert-stream-broker chart, which defaults to "3.4.0".

When upgrading the Kafka version, you also may need to update the ``kafka.logMesageFormatVersion`` and ``kafka.interBrokerProtocolVersion``.
These change slowly, but old values can be incompatible with new Kafka versions.
See `Strimzi documentation on Kafka Versions <https://strimzi.io/docs/operators/latest/full/deploying.html#ref-kafka-versions-str>`__ to be sure.

So, to update the version of Kafka used, update the `applications/alert-stream-broker/values-usdfdev-alert-stream-broker.yaml
<https://github.com/lsst-sqre/phalanx/blob/main/applications/alert-stream-broker/values-usdfdev-alert-stream-broker.yaml>`__ file in `github.com/lsst-sqre/phalanx`_.
Under ``alert-stream-broker``, then under ``kafka``, add a value: ``version: <whatever you want>``.
 ``logMessageFormatVersion`` and ``interBrokerProtocolVersion`` are now set automatically and do not need to be manually set.

Then, follow the steps in :ref:`deploying-a-change` to apply these changes.

See also: the Strimzi Documentation's "`9.5: Upgading Kafka <https://strimzi.io/docs/operators/latest/full/deploying.html#assembly-upgrading-kafka-versions-str>`__".

Updating the Strimzi version
----------------------------
The current version of Strimzi used by the Alert Broker is updated and managed by Square. Any changes to the version should be
discussed with them. If any specific changes are required, you probably want to read the Strimzi Documentation's "`9. Upgrading Strimzi <https://strimzi.io/docs/operators/latest/full/deploying.html#assembly-upgrade-str>`__".
The Strimzi application does not automatically sync to the latest version on phalanx and must be manually synced. This is to
prevent Strimzi from automatically updated to a version which does not support the current Kafka version used by the Alert Broker.
This requires monitoring of the Strimzi version supported by Square to keep both the Kafka version and Strimzi version in sync.

The Strimzi version version is governed by the version referenced in `github.com/lsst-sqre/phalanx`_'s `applications/strimzi/Chart.yaml <https://github.com/lsst-sqre/phalanx/tree/main/applications//strimzi/Chart.yaml#L9>`__ file.

Then, apply the change in a way similar to that described in :ref:`deploying-a-change`.
Note though that you'll be synchronizing the 'strimzi' application in Argo, not the 'alert-stream-broker' application in Argo.

Resizing Kafka broker disk storage
----------------------------------

Some reference reading:

 - DMTN-210's section `3.2.1.3: Storage <https://dmtn-210.lsst.io/#storage>`__.
 - "`Persistent storage improvements <https://strimzi.io/blog/2019/07/08/persistent-storage-improvements/>`__"

Change the alert-stream-broker.kafka.storage.size value in `applications/alert-stream-broker/values-usdfdev-alert-stream-broker.yaml`_ in `github.com/lsst-sqre/phalanx`_.
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
For example, the current latest version as of this writing is 5.0, so there's a python/lsst/alert/packet/schema/5/0 directory which holds Avro schemas.
You could put a new schema in python/lsst/alert/packet/schema/5/1.

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

The defaults are set in the alert-stream-schema-registry's `values.yaml <https://github.com/lsst-sqre/phalanx/blob/main/applications/alert-stream-broker/charts/alert-stream-schema-registry/values.yaml>`__ file.
You can update the defaults, or you can update the parameters used in Phalanx for a particular environment under the `alert-stream-schema-registry <https://github.com/lsst-sqre/phalanx/blob/main/applications/alert-stream-broker/values-usdfdev-alert-stream-broker.yaml>`__ field.

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



Schema Registry Ids
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Schema ids are determined by the schema version number. Ids are assigned using the major number and assigning the minor number
to a 00 format. For example, schema version 7.1 will be schema id number 701. Schema 13.12 would be schema 1312 and so forth.

These ids are generated automatically from the schemas within `lsst/alert/packet/schema`_ in `github.com/lsst/alert_packet`_,
and are assigned to the registry in `syncAllSchemasToRegistry.py`_.
Corresponding ids are assigned to alerts in `packageAlerts.py`_.

Kowl is the easiest way to view current schema ids and the schema id used for specific alerts.

Run Kowl (see :ref:`running-kowl`) and then navigate to http://localhost:8080/schema-registry/alert-packet.
There should be a drop-down with different versions. You probably want the latest version, which might already be the one being displayed.
Select the desired version.

At the top of the screen, you should see the "Schema ID" of the schema you have selected.

Updating the Alert Stream Simulator values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You're almost done.
We need to update the alert stream simulator deployment to use the new container version, and to use the new schema ID.

The container version is set in `values-usdfdev-alert-stream-broker.yaml's alert-stream-simulator.image.tag <https://github.com/lsst-sqre/phalanx/blob/main/applications/alert-stream-broker/values-usdfdev-alert-stream-broker.yaml#L122>`__ field.
Update this to match the tag you used in github.com/lsst-dm/alert-stream-simulator.

The schema ID can be set in values-usdfdev-alert-stream-broker.yaml as well, under ``alert-stream-simulator.schemaID``.
This is set to ``1`` by default.

Those changes to values-usdfdev-alert-stream-broker.yaml are half the story.
You probably also should update the defaults, which is done by editing the `values.yaml <https://github.com/lsst-sqre/phalanx/blob/main/applications/alert-stream-broker/charts/alert-stream-simulator/values.yaml>`__ files in the alert-stream-simulator chart.
This values.yaml changes the dynamic configurations on a topic level, which override any settings, such as retention.ms or retention.bytes set on a broker level.

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
   This means there should be some "environment" analogous to "usdf" which is used in the USDF integration deployment.
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

.. _schema-registry-dns:

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
The following information is only relevant if you are setting up an independent alert broker environment.

You'll need to configure a new Phalanx deployment.

To do this, create a ``values-<environment>.yaml`` file in the `applications/alert-stream-broker`_ directory of `github.com/lsst-sqre/phalanx`_ which matches the environment.

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

.. _broker-dns:

Provisioning DNS records
~~~~~~~~~~~~~~~~~~~~~~~~

Once the alert-stream-broker is synced into a half-broken, half-working state, we can start to get the IP addresses used by its services.
This will let us provision more DNS records: those for the Kafka brokers.

In  the current gcloud setup, this must be done through Square. If you cannot use the existing static IPs, you must
request that you are assigned six for the Kafka brokers, and that the DNS records are updated to point to the correct
static IPs.

You will then need to update ``values-idfint.yaml``:

.. code-block::

    alert-stream-broker:
      cluster:
        name: "alert-broker"

      kafka:
        # Addresses based on the state as of 2022-11-06; these were assigned by
        # Square and now we're pinning them.
        externalListener:
          tls:
            enabled: true
          bootstrap:
            ip: 35.224.176.103
            host: alert-stream-int.lsst.cloud
          brokers:
            - ip: "34.28.80.188"
            host: alert-stream-int-broker-0.lsst.cloud
            - ip: "35.188.136.140"
            host: alert-stream-int-broker-1.lsst.cloud
            - ip: "35.238.84.221"
            host: alert-stream-int-broker-2.lsst.cloud



The Kafka brokers MUST point to static IPs, as restarting Kafka will otherwise result in the assigned IP's to change.
If they do not, there will be problems with the SSL certificates and he users will not be able to connect. See the following
link for an explanation on why:

https://strimzi.io/blog/2021/05/07/deploying-kafka-with-lets-encrypt-certificates/

If the pods have been deleted and re-starting them results in new IP's being automatically assigned or you see the following error,
the previous pods were not deleted and may be orphaned. If you cannot see them via kubectl, you must get in contact
with a kubernetes admin and have them delete the service. This may look like the following.

.. code-block:: sh

    Failed to allocate IP for "alert-stream-broker/alert-broker-kafka-8": can't change sharing key for "alert-stream-broker/alert-broker-kafka-8", address also in use by vcluster--usdf-alert-stream-broker-dev/alert-broker-kafka-2-x-alert-stream-broker-x-vcluste-90c3cd7783

Previous DNS provisioning workflow
~~~~~~~~~~~~~~~~~~~~~~~~

To provision the Kafka broker IPs, we will use :command:`kubectl` to look up the IP addresses provisioned for the broker (see :ref:`kubectl`).

Run :command:`kubectl get service --namespace alert-stream-broker` to get a list of all the services running:

.. code-block:: sh

    -> % kubectl get service  -n alert-stream-broker
    NAME                                    TYPE           CLUSTER-IP       EXTERNAL-IP     PORT(S)                               AGE
    alert-broker-kafka-10                   LoadBalancer   10.108.207.210   134.79.23.217   9094:31234/TCP                                 24h
    alert-broker-kafka-11                   LoadBalancer   10.97.120.2      134.79.23.219   9094:31858/TCP                                 24h
    alert-broker-kafka-6                    LoadBalancer   10.96.28.225     134.79.23.214   9094:30302/TCP                                 24h
    alert-broker-kafka-7                    LoadBalancer   10.108.145.98    134.79.23.216   9094:30747/TCP                                 24h
    alert-broker-kafka-8                    LoadBalancer   10.108.169.180   134.79.23.218   9094:31850/TCP                                 24h
    alert-broker-kafka-9                    LoadBalancer   10.101.139.74    134.79.23.220   9094:32476/TCP                                 24h
    alert-broker-kafka-bootstrap            ClusterIP      10.99.56.206     <none>          9091/TCP,9092/TCP,9093/TCP                     24h
    alert-broker-kafka-brokers              ClusterIP      None             <none>          9090/TCP,9091/TCP,8443/TCP,9092/TCP,9093/TCP   24h
    alert-broker-kafka-external-bootstrap   LoadBalancer   10.111.167.245   134.79.23.185   9094:30280/TCP                                 24h
    alert-schema-registry                   ClusterIP      10.104.135.221   <none>          8081/TCP                                       23h
    alert-stream-broker-alert-database      ClusterIP      10.99.69.201     <none>          3000/TCP                                       23h                            49d


The important column here is "EXTERNAL-IP."
Use it to discover the IP addresses for each of the individual broker hosts, and for the "external-bootstrap" service.
Request DNS A records that map useful hostnames to these IP addresses - this is done by the SQuARE team, so you'll need help.

Once you have DNS provisioned, make another change to ``values-<environment>.yaml`` to lock in the IP addresses and inform Kafka of the hostnames to use.
For example, here's ``values-idfint.yaml``:

Apply this change as usual (see :ref:`deploying-a-change`).
Now the broker *should* be accessible.

Adding users
~~~~~~~~~~~~

Make new user credential sets in 1Password for the new targeted environment.
See :ref:`new-user` for how to do this.

In addition, make a user named 'kafka-admin' in 1Password in the same way.

Make sure to use the right value for the ``environment`` field of the 1Password items.

Then, set ``alert-stream-broker.vaultSecretsPath`` in ``values-<environment>.yaml`` to ``secret/k8s_oeprator/<environment>/alert-stream-broker``. This will configure the Vault Secrets Operator to correctly feed secrets through.

Lingering issues
~~~~~~~~~~~~~~~~

You may need to re-sync several times to trigger the data-loading job of the alert stream simulator.
When the system is in its half-broken state, this job will fail, and it can exponentially back-off which can take a very long time to recover.
It can also hit a max retry limit and stop attempting to load data.

Using Argo to "sync" will kick it off again, which may fix the problem.

Testing connectivity
~~~~~~~~~~~~~~~~~~~~

You should now have a working cluster.
You should be able to run Kowl with the new superuser identity and it ought to be able to connect.

Deploying on a new Kubernetes cluster off of Google
---------------------------------------------------

Deploying to a new Kubernetes cluster off of Google will require all the same steps as described in the previous section, but with a few additional wrinkles.

First, the alert-stream-broker chart uses the "load balancer" service type to provide external internet access to the Kafka nodes.
Load balancer services are very platform-specific; on Google it corresponds to creation of TCP Load Balancers.
On a non-Google platform, it might work very differently.

One option would be to use the targeted platform's load balancers.
Another option is to use Node Ports or Ingresses instead.
The 5-part Strimzi blog post series "`Accessing Kafka <https://strimzi.io/blog/2019/04/17/accessing-kafka-part-1/>`__" goes into detail about these options.

Second, the alert database uses Google Cloud Storage buckets to store raw alert and schema data.
This would need to be replaced with something appropriate for the targeted environment.
The requirements are made clear in the ``storage.py`` files of the `github.com/lsst-dm/alert_database_ingester`_ and `github.com/lsst-dm/alert_database_server`_ repositories.
An implementation would need to fulfill the abstract interface provided in that file.

There may be more requirements, but there certainly needs to be an investigation if you're planning to move to a different Kubernetes provider.

Changing the schema registry hostname
-------------------------------------

The Schema Registry's hostname is controlled by the 'hostname' value passed in to `charts/alert-stream-schema-registry`_.
Updating that will update the hostname expected by the service.

In addition, a new DNS record will need to be created by whoever is provisioning DNS for the target environment.
For the USDF environment, that's SQuARE.
It should route the new hostname to the ingress IP address.

Finally, the new schema registry needs to be passed in to the alert database in its ``ingester.schemaRegistryURL`` value.

See also: :ref:`schema-registry-dns`.

Changing the Kafka broker hostnames
-----------------------------------

Kafka broker hostnames can be changed by modifying the values passed in to  `charts/alert-stream-broker`_.
Once changed, the broker will not work until DNS records are also updated.

See also: :ref:`broker-dns`.

Changing the alert database URL
-------------------------------

The alert database's URL is based off of that of the cluster's main Gafaelfawr ingress, so it cannot be changed entirely.
However, it uses a path prefix, which *can* be changed.
This path prefix is controlled by a value passed in to the alert database chart.

Changing the Kafka hardware
---------------------------

To change the hardware used by Kafka, change the nodes used in the node pool.
This is set in the terraform configuration in `environment/deployments/science-platform/env/integration-gke.tfvars <https://github.com/lsst/idf_deploy/blob/main/environment/deployments/science-platform/env/integration-gke.tfvars#L48-L64>`__:

.. code-block:: terraform

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


Change this, and apply the terraform change.

This may cause some downtime as the kafka nodes are terminated and replaced with new ones, evicting the Kafka brokers, but this isn't known for certain.

.. _Google Cloud Platform's console: https://console.cloud.google.com/home/dashboard?project=science-platform-int-dc5d
.. _github.com/lsst-sqre/phalanx: https://github.com/lsst-sqre/phalanx
.. _alert-stream-broker/charts: https://github.com/lsst-sqre/phalanx/tree/main/applications/alert-stream-broker/charts
.. _github.com/lsst/idf_deploy: https://github.com/lsst/idf_deploy
.. _github.com/lsst/alert_packet: https://github.com/lsst/alert_packet
.. _packageAlerts.py: https://github.com/lsst/ap_association/blob/main/python/lsst/ap/association/packageAlerts.py
.. _lsst/alert/packet/schema: https://github.com/lsst/alert_packet/tree/main/python/lsst/alert/packet/schema
.. _syncAllSchemasToRegistry: https://github.com/lsst/alert_packet/blob/main/python/lsst/alert/packet/bin/syncAllSchemasToRegistry.py
.. _github.com/lsst-dm/alert-stream-simulator: https://github.com/lsst-dm/alert-stream-simulator
.. _github.com/lsst-dm/alert_database_ingester: https://github.com/lsst-dm/alert_database_ingester
.. _github.com/lsst-dm/alert_database_server: https://github.com/lsst-dm/alert_database_server
.. _applications/alert-stream-broker: https://github.com/lsst-sqre/phalanx/tree/main/applications/alert-stream-broker
.. _applications/alert-stream-broker/Chart.yaml: https://github.com/lsst-sqre/phalanx/blob/main/applications/alert-stream-broker/Chart.yaml
.. _applications/alert-stream-broker/values-usdfdev-alert-stream-broker.yaml: https://github.com/lsst-sqre/phalanx/blob/main/applications/alert-stream-broker/values-usdfdev-alert-stream-broker.yaml
.. _charts/alert-stream-broker: https://github.com/lsst-sqre/phalanx/tree/main/applications/alert-stream-broker/charts/alert-stream-broker
.. _charts/alert-stream-schema-registry: https://github.com/lsst-sqre/phalanx/tree/main/applications/alert-stream-broker/charts/alert-stream-schema-registry
.. _science-platform: https://data-int.lsst.cloud/argo-cd/applications/argocd/science-platform?view=tree&resource=
.. _usdf-alert-stream-broker-dev: https://k8s.slac.stanford.edu/usdf-alert-stream-broker-dev/argo-cd/applications/argocd/usdf-alert-stream-broker-dev?view=tree
.. _kafka.yaml: https://github.com/lsst-sqre/phalanx/blob/main/applications/alert-stream-broker/charts/alert-stream-broker/templates/kafka.yaml
.. _values-usdfdev-alert-stream-broker.yaml:: https://github.com/lsst-sqre/phalanx/blob/main/applications/alert-stream-broker/values-usdfdev-alert-stream-broker.yaml


.. rubric:: References

.. bibliography:: local.bib lsstbib/books.bib lsstbib/lsst.bib lsstbib/lsst-dm.bib lsstbib/refs.bib lsstbib/refs_ads.bib
    :style: lsst_aa
