eventing.main
=============

.. py:module:: eventing.main

.. autoapi-nested-parse::

   FastAPI application entrypoint for the eventing service.



Attributes
----------

.. autoapisummary::

   eventing.main.app


Functions
---------

.. autoapisummary::

   eventing.main.create_app
   eventing.main.lifespan


Module Contents
---------------

.. py:function:: create_app()

   Create the FastAPI app instance.


.. py:function:: lifespan(app)
   :async:


   Initialize and tear down outbox infrastructure for the service.


.. py:data:: app

