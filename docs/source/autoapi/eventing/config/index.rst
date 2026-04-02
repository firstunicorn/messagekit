eventing.config
===============

.. py:module:: eventing.config

.. autoapi-nested-parse::

   Runtime settings for the eventing service.



Attributes
----------

.. autoapisummary::

   eventing.config.settings


Classes
-------

.. autoapisummary::

   eventing.config.Settings


Module Contents
---------------

.. py:class:: Settings(_case_sensitive = None, _nested_model_default_partial_update = None, _env_prefix = None, _env_prefix_target = None, _env_file = ENV_FILE_SENTINEL, _env_file_encoding = None, _env_ignore_empty = None, _env_nested_delimiter = None, _env_nested_max_split = None, _env_parse_none_str = None, _env_parse_enums = None, _cli_prog_name = None, _cli_parse_args = None, _cli_settings_source = None, _cli_parse_none_str = None, _cli_hide_none_type = None, _cli_avoid_json = None, _cli_enforce_required = None, _cli_use_class_docs_for_groups = None, _cli_exit_on_error = None, _cli_prefix = None, _cli_flag_prefix_char = None, _cli_implicit_flags = None, _cli_ignore_unknown_args = None, _cli_kebab_case = None, _cli_shortcuts = None, _secrets_dir = None, _build_sources = None, **values)

   Bases: :py:obj:`fastapi_config_patterns.BaseFastAPISettings`, :py:obj:`fastapi_config_patterns.BaseDatabaseSettings`


   Application settings loaded from environment variables.


   .. py:attribute:: model_config

      Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].


   .. py:attribute:: service_name
      :type:  str
      :value: None



   .. py:attribute:: api_prefix
      :type:  str
      :value: None



   .. py:attribute:: database_url
      :type:  str
      :value: None



   .. py:attribute:: kafka_bootstrap_servers
      :type:  str
      :value: None



   .. py:attribute:: kafka_client_id
      :type:  str
      :value: None



   .. py:attribute:: outbox_batch_size
      :type:  int
      :value: None



   .. py:attribute:: outbox_poll_interval_seconds
      :type:  int
      :value: None



   .. py:attribute:: outbox_max_retry_count
      :type:  int
      :value: None



   .. py:attribute:: outbox_retry_backoff_multiplier
      :type:  float
      :value: None



   .. py:attribute:: outbox_worker_enabled
      :type:  bool
      :value: None



.. py:data:: settings

