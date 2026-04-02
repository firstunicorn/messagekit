eventing.infrastructure.messaging.kafka_consumer_base
=====================================================

.. py:module:: eventing.infrastructure.messaging.kafka_consumer_base

.. autoapi-nested-parse::

   Idempotent consumer base with simple in-memory deduplication.



Classes
-------

.. autoapisummary::

   eventing.infrastructure.messaging.kafka_consumer_base.IdempotentConsumerBase


Module Contents
---------------

.. py:class:: IdempotentConsumerBase

   Bases: :py:obj:`abc.ABC`


   Skip duplicate events by event identifier within the process lifetime.


   .. py:method:: consume(message)
      :async:


      Process a message once, returning whether work was performed.



   .. py:method:: handle_event(message)
      :abstractmethod:

      :async:


      Handle one deserialized event payload.



