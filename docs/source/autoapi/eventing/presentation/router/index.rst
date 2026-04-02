eventing.presentation.router
============================

.. py:module:: eventing.presentation.router

.. autoapi-nested-parse::

   Top-level router registration for the eventing service.



Attributes
----------

.. autoapisummary::

   eventing.presentation.router.api_router


Functions
---------

.. autoapisummary::

   eventing.presentation.router.health
   eventing.presentation.router.outbox_health


Module Contents
---------------

.. py:data:: api_router

.. py:function:: health()
   :async:


   Return a basic service health payload.


.. py:function:: outbox_health(request)
   :async:


   Return outbox infrastructure health if it has been initialized.


