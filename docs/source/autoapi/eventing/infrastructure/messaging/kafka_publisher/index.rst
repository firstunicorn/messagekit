eventing.infrastructure.messaging.kafka_publisher
=================================================

.. py:module:: eventing.infrastructure.messaging.kafka_publisher

.. autoapi-nested-parse::

   Kafka-backed event publisher built on FastStream.



Classes
-------

.. autoapisummary::

   eventing.infrastructure.messaging.kafka_publisher.KafkaEventPublisher


Module Contents
---------------

.. py:class:: KafkaEventPublisher(broker)

   Bases: :py:obj:`python_outbox_core.IEventPublisher`


   Publish serialized events to Kafka topics derived from event type.


   .. py:method:: publish(message)
      :async:


      Publish a message to its default event topic.



   .. py:method:: publish_to_topic(topic, message)
      :async:


      Publish a message to an explicit Kafka topic.



