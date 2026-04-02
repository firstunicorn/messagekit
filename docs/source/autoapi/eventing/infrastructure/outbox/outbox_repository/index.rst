eventing.infrastructure.outbox.outbox_repository
================================================

.. py:module:: eventing.infrastructure.outbox.outbox_repository

.. autoapi-nested-parse::

   SQLAlchemy implementation of the outbox repository contract.



Classes
-------

.. autoapisummary::

   eventing.infrastructure.outbox.outbox_repository.SqlAlchemyOutboxRepository


Module Contents
---------------

.. py:class:: SqlAlchemyOutboxRepository(session_factory, registry)

   Bases: :py:obj:`python_outbox_core.IOutboxRepository`


   Persist and retrieve outbox events with SQLAlchemy async sessions.


   .. py:method:: add_event(event)
      :async:


      Store a serialized event without committing the transaction.



   .. py:method:: get_unpublished(limit = 100, offset = 0)
      :async:


      Fetch unpublished events ordered by creation time.



   .. py:method:: mark_published(event_id)
      :async:


      Mark an event as published and timestamp the update.



   .. py:method:: count_unpublished()
      :async:


      Count pending unpublished and non-failed events.



   .. py:method:: mark_failed(event_id, error_message)
      :async:


      Persist failure state and error details for an event.



   .. py:method:: ping()
      :async:


      Check if the backing database is reachable.



   .. py:method:: oldest_unpublished_age_seconds()
      :async:


      Return the age of the oldest pending event in seconds.



