eventing.infrastructure.messaging.dead_letter_handler
=====================================================

.. py:module:: eventing.infrastructure.messaging.dead_letter_handler

.. autoapi-nested-parse::

   Dead-letter routing for permanently failed events.



Classes
-------

.. autoapisummary::

   eventing.infrastructure.messaging.dead_letter_handler.DeadLetterHandler


Module Contents
---------------

.. py:class:: DeadLetterHandler(repository, publisher)

   Mark failed outbox records and publish them to a DLQ topic.


   .. py:method:: handle(event, error_message)
      :async:


      Persist failure details and publish the event to its DLQ topic.



