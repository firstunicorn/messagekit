eventing.infrastructure.health.outbox_health_check
==================================================

.. py:module:: eventing.infrastructure.health.outbox_health_check

.. autoapi-nested-parse::

   Health check adapter for outbox and broker infrastructure.



Classes
-------

.. autoapisummary::

   eventing.infrastructure.health.outbox_health_check.EventingHealthCheck


Module Contents
---------------

.. py:class:: EventingHealthCheck(repository, broker, lag_threshold = 1000, stale_after_seconds = 300)

   Bases: :py:obj:`python_outbox_core.health_check.OutboxHealthCheck`


   Aggregate database, broker, and outbox lag health signals.


   .. py:method:: check_health()
      :async:


      Return a combined health payload for the outbox subsystem.



   .. py:method:: check_database()
      :async:


      Check whether the repository database can answer a ping.



   .. py:method:: check_broker()
      :async:


      Check whether the Kafka broker is reachable.



   .. py:method:: check_outbox_lag()
      :async:


      Report unpublished count and age of the oldest pending event.



