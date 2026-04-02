eventing.infrastructure.outbox.outbox_worker
============================================

.. py:module:: eventing.infrastructure.outbox.outbox_worker

.. autoapi-nested-parse::

   Retrying outbox worker with DLQ fallback.



Classes
-------

.. autoapisummary::

   eventing.infrastructure.outbox.outbox_worker.ScheduledOutboxWorker


Module Contents
---------------

.. py:class:: ScheduledOutboxWorker(repository, publisher, config, dead_letter_handler = None)

   Bases: :py:obj:`python_outbox_core.OutboxPublisherBase`


   Publish outbox events on a polling loop with retry and DLQ support.


   .. py:method:: schedule_publishing()
      :async:


      Run a polling loop until stop() is called.



   .. py:method:: stop()
      :async:


      Signal the worker loop to exit.



