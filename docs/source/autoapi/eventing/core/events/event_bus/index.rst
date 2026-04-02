eventing.core.events.event_bus
==============================

.. py:module:: eventing.core.events.event_bus

.. autoapi-nested-parse::

   Decorator-friendly facade for in-process event dispatch.



Attributes
----------

.. autoapisummary::

   eventing.core.events.event_bus.EventCallback
   eventing.core.events.event_bus.HandlerLike


Classes
-------

.. autoapisummary::

   eventing.core.events.event_bus.RegisteredHandler
   eventing.core.events.event_bus.DispatchBackend
   eventing.core.events.event_bus.SequentialDispatchBackend
   eventing.core.events.event_bus.EventBus


Module Contents
---------------

.. py:data:: EventCallback

.. py:data:: HandlerLike

.. py:class:: RegisteredHandler

   Store one registered callback with its display name.


   .. py:attribute:: name
      :type:  str


   .. py:attribute:: callback
      :type:  EventCallback


.. py:class:: DispatchBackend

   Bases: :py:obj:`Protocol`


   Execute one dispatch strategy.


   .. py:attribute:: name
      :type:  str


   .. py:method:: invoke(event, handlers, invoke_one)
      :async:


      Run the provided handlers for one event.



.. py:class:: SequentialDispatchBackend

   Dispatch handlers sequentially in registration order.


   .. py:attribute:: name
      :value: 'sequential'



   .. py:method:: invoke(event, handlers, invoke_one)
      :async:



.. py:class:: EventBus(*, backend = None, hooks = None, settings = None)

   Provide a higher-level event emitter/subscriber facade.


   .. py:method:: register(event_type, handler, *, handler_name = None)

      Register one handler instance or async callback.



   .. py:method:: subscriber(event_type, *, handler_name = None)

      Register an async callback through a decorator.



   .. py:method:: dispatch(event)
      :async:


      Dispatch one event through the configured backend.



