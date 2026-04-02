eventing.infrastructure.persistence.outbox_orm
==============================================

.. py:module:: eventing.infrastructure.persistence.outbox_orm

.. autoapi-nested-parse::

   SQLAlchemy ORM model for transactional outbox storage.



Classes
-------

.. autoapisummary::

   eventing.infrastructure.persistence.outbox_orm.OutboxEventRecord


Module Contents
---------------

.. py:class:: OutboxEventRecord

   Bases: :py:obj:`eventing.infrastructure.persistence.orm_base.Base`


   Persisted event waiting to be published to Kafka.


   .. py:attribute:: event_id
      :type:  sqlalchemy.orm.Mapped[str]


   .. py:attribute:: event_type
      :type:  sqlalchemy.orm.Mapped[str]


   .. py:attribute:: aggregate_id
      :type:  sqlalchemy.orm.Mapped[str]


   .. py:attribute:: payload
      :type:  sqlalchemy.orm.Mapped[dict[str, Any]]


   .. py:attribute:: occurred_at
      :type:  sqlalchemy.orm.Mapped[datetime.datetime]


   .. py:attribute:: published
      :type:  sqlalchemy.orm.Mapped[bool]


   .. py:attribute:: failed
      :type:  sqlalchemy.orm.Mapped[bool]


   .. py:attribute:: created_at
      :type:  sqlalchemy.orm.Mapped[datetime.datetime]


   .. py:attribute:: published_at
      :type:  sqlalchemy.orm.Mapped[datetime.datetime | None]


   .. py:attribute:: failed_at
      :type:  sqlalchemy.orm.Mapped[datetime.datetime | None]


   .. py:attribute:: error_message
      :type:  sqlalchemy.orm.Mapped[str | None]


