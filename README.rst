|header|

.. |header| image:: https://github.com/koales/telepack/raw/main/img/telepack.png
    
telepack
========

`telepack` makes adding observability to your Python code as effortless as possible. It provides a high-level abstraction over New Relic's `newrelic-telemetry-sdk <https://pypi.org/project/newrelic-telemetry-sdk/>`_ (thanks to New Relic for providing an SDK for their API). Telemetry data, including traces, spans, and custom metrics, is then available for analysis in the New Relic One platform.

A primary use case for this library is expected to be by data scientists and software engineers working with Jupyter Notebooks.  `telepack` is designed to be straightforward, unobtrusive, and quick to implement, allowing you to focus on your core tasks while seamlessly adding observability.  Of course, you can use `telepack` anywhere you find it helpful!

`telepack` handles the complexities of trace, span, and metric management, enabling you to easily instrument your code with minimal effort. `telepack`'s goal is to increase the democratisation of observability for everyone.

Pre-requisites
--------------

To use `telepack`, you will need a New Relic account and an API key. If you don't have a New Relic account, you can sign up for a free account at `New Relic <https://newrelic.com/>`_.

Brief Overview of Traces, Spans, and Metrics
--------------------------------------------

Understanding the basic concepts of tracing and metrics will be helpful.

A **trace** represents a single operation or task (or subtask) that you want to monitor. It is composed of one or more **spans**. A span is a single unit of work (or subtask) *within* a trace.  For example, a trace might represent a complete data processing pipeline, and each span could represent a single step in that pipeline.

**Metrics** are numerical measurements that track the performance and behavior of your application over time. They provide insights into key aspects of your system, such as resource utilization, latency, and throughput, or number of tokens used by an language model in undersanding your prompt and in generating a completion response.

Key Features
------------

Span and Traces
~~~~~~~~~~~~~~~

* **Effortless Instrumentation:** Provides two simple interfaces: the `@timed` decorator for timing function calls and the `TimedContext` context manager for timing arbitrary code blocks.
* **Automatic Trace and Span Management:** `telepack` automatically creates traces (collections of spans), manages the lifecycle of spans, and uploads them to New Relic. This automatic behavior is the default, but you can override it if needed (see Advanced Usage).
* **Automatic Trace Start Detection:** A new trace begins when a top-level span (a span without a parent) is initiated. Calling a decorated function or entering a timed context outside of any existing timed block will automatically start a new trace.
* **Nested Span Support:** Parent-child span relationships are captured automatically, preserving the hierarchical structure of your code's execution within New Relic. This provides a clear visual representation of your code's execution flow.
* **Simplified Timing:** Timing a function is as simple as adding the `@timed` decorator before the function definition. The span is automatically named with the function's name, or you can provide a custom name.
* **Flexible Configuration:** You can define timed functions *before* configuring the logger. `telepack` will queue the spans until the logger is configured. This lets you organize your code as you prefer.
* **Manual Processing (Optional, Advanced):** While automatic processing is recommended for simplicity, manual control is available if you need more fine-grained control.

Metrics
~~~~~~~

* **Metric Logging:** Send custom metrics to New Relic to monitor application performance and behavior. Includes support for gauge metrics, LLM token metrics, and OpenAI completion metrics.
* **Metric Batching and Individual Sends:** Configure `telepack` to send metrics in batches or individually as they are logged.
* **Metric Context Manager:** Use the `MetricLoggerCM` context manager for convenient metric logging and automatic flushing.

Common Features
~~~~~~~~~~~~~~~

* **EU Region Support:** The EU (Europe) region API endpoint for New Relic is automatically configured when you specify the `eu_hosted` flag.
* **Kaggle Secrets Integration (Optional):** When working in Kaggle Notebooks, the New Relic API key can be automatically retrieved from Kaggle Secrets (best practice for keeping secrets secret).

Traces and Spans in New Relic
-----------------------------

For a trace to appear in the New Relic UI:

* It must contain at least one span. Only spans are reported to New Relic, and each span includes a trace ID to link it to other spans in the same trace.
* You must provide a `client_service_name` and `client_host`. These identify the source of the telemetry data. Use meaningful values, e.g., `data_processing_pipeline` and `hosted_jupyter.example.com` (note: `client_host` doesn't have to be a domain name, any descriptive text will work).

Installation
------------

.. code-block:: bash

    pip install telepack

This command installs `telepack` and all its dependencies, including `newrelic-telemetry-sdk`.

Usage
-----

Configuration
~~~~~~~~~~~~~

The ``TraceLogger`` and ``MetricLogger`` *must* be initialized before spans and metrics can be sent to New Relic.

**Important Note:** For tracing, you can decorate functions *before* configuring `TraceLogger`. This allows you flexibility in how you structure your code.

.. code-block:: python

    from telepack import TraceLogger, MetricLogger

    tl = TraceLogger(
        "my_service_name",  # Your service name
        "my_host",          # Your host name
        use_kaggle_secret=True,  # Set to True to use Kaggle Secrets
        licence_key_secret_name="NEW_RELIC_LICENSE_KEY",  # Name of your Kaggle Secret
        eu_hosted=True # Set to True if your New Relic account is EU hosted
    )

    # Or, provide the license key directly:
    # tl = TraceLogger("my_service_name", "my_host", license_key="YOUR_NEW_RELIC_LICENSE_KEY")

    ml = MetricLogger(
        use_kaggle_secret=True,
        license_key_secret_name="NEW_RELIC_LICENSE_KEY",
        eu_hosted=True,
        metric_prefix="my_prefix" # Optional metric prefix to be prefixed to all metric names
    )

Using the ``@timed`` decorator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from telepack import timed

    @timed  # Times the function; span name defaults to the function name
    def my_function():
        # Your code here
        ...

    @timed(span_name="My Custom Span Name")  # Times the function with a custom span name
    def another_function():
        # Your code here
        ...

    my_function()
    another_function()

Using the ``TimedContext`` context manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from telepack import TimedContext

    with TimedContext("My Code Block"):
        # Your code here
        ...

Metric Logging
~~~~~~~~~~~~~~

.. code-block:: python

    from telepack import MetricLogger, GaugeMetric, LLMTokensMetric, OpenAICompletionMetric, MetricLoggerCM
    from kaggle_secrets import UserSecretsClient
    from openai import OpenAI

    ml = MetricLogger(use_kaggle_secret=True, license_key_secret_name="NEW_RELIC_LICENSE_KEY", eu_hosted=True, metric_prefix="example")

    ml.log(GaugeMetric("test_metric", 42, "Units"))
    ml.log(GaugeMetric("test_metric", 59, "Units", {"key1": "value1", "key2": "value2"}))
    ml.log(LLMTokensMetric("gpt-2", "inference", 1000))
    ml.log(LLMTokensMetric("gpt-2", "inference", 1000, tags={"key1": "value1", "key2": "value2"}))

    # Example of logging OpenAI completion metrics
    OPENAI_BASE_URL = "https://api.scaleway.ai/v1"
    openai_key = UserSecretsClient().get_secret("OPENAI_API_KEY")
    openai = OpenAI(base_url=OPENAI_BASE_URL, api_key=openai_key)
    completion = openai.chat.completions.create(model="llama-3.1-8b-instruct", messages=[{"role": "user", "content": "Hello"}])
    ml.log(OpenAICompletionMetric(completion))

    # Using the MetricLoggerCM context manager for automatic flushing
    with MetricLoggerCM(ml):
        ml.log(GaugeMetric("context_metric", 100, "Count"))

Advanced Usage
--------------

Setting Trace IDs (Optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While `telepack` automatically manages trace creation, you can set a specific trace ID for advanced use cases, such as correlating operations across different parts of your application.

.. code-block:: python

   TraceLogger.new_trace("my_trace_id")  # Set a custom trace ID
   my_function()  # Spans logged within this call will use the specified trace ID
   TraceLogger.new_trace()  # Reset to auto-generated trace IDs

This is useful for tracking a larger operation (possibly a distributed workload) as a single trace.

Disabling/Enabling Tracing (Optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Recording and sending of traces is automatically enabled when the logger is configured. It can be manually controlled if needed.

.. code-block:: python
   
   TraceLogger.disable() # Disable tracing
   my_function() # No spans will be logged
   TraceLogger.enable() # Re-enable tracing
   my_function() # Spans will be logged

Tracing is disabled when the logger has not yet been initialised. This enables functions to be declared, decorated and even called (without exceptions from the logger being raised), before the logger is configured.

Tracing is then enabled when the logger is configured. Spans will be logged from this point onwards.

Thereafter, tracing can be disabled and re-enabled manually as required.

Batched or Individual Span Uploads (Optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, spans are collected and uploaded to New Relic in batches. You can configure `telepack` to send spans one at a time, as they complete.

.. code-block:: python

   from telepack import TraceLogger, timed

   tl = TraceLogger(
           "my_service_name",  # Your service name
           "my_host",        # Your host name
           license_key="YOUR_NEW_RELIC_LICENSE_KEY",  # Your New Relic API key
           batch_send=False   # Set to False to send spans individually
           )

   @timed
   def my_function():
       # Your code here
       ...

   my_function()  # Span will be sent immediately (and will be its own trace)

Manual Flushing of Spans (Optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default (in batch mode), spans are sent to New Relic when a trace completes. You can disable automatic flushing and flush spans manually.

.. code-block:: python

   from telepack import TraceLogger, timed

   tl = TraceLogger(
           "my_service_name",  # Your service name
           "my_host",        # Your host name
           license_key="YOUR_NEW_RELIC_LICENSE_KEY",  # Your New Relic API key
           auto_flush=False   # Set to False to disable automatic flushing
           )

   @timed
   def my_function():
       # Your code here
       ...

   my_function()  # Span will be cached locally

   TraceLogger.flush()  # Manually send the cached spans

Example
-------

.. code-block:: python

    from telepack import TraceLogger, timed, TimedContext, MetricLogger, GaugeMetric, LLMTokensMetric, OpenAICompletionMetric, MetricLoggerCM
    import time
    from kaggle_secrets import UserSecretsClient
    from openai import OpenAI

    @timed
    def task_one():
        time.sleep(0.5)
        with TimedContext("Subtask"):
            time.sleep(0.2)
        time.sleep(0.3)

    @timed(span_name="Task Two")
    def task_two():
        time.sleep(1)

    tl = TraceLogger(
        "my_service_name",  # Your service name
        "my_host",          # Your host name
        license_key="YOUR_NEW_RELIC_LICENSE_KEY",  # Set to your New Relic API license key
    )

    task_one()
    task_two()

    ml = MetricLogger(use_kaggle_secret=True, license_key_secret_name="NEW_RELIC_LICENSE_KEY", eu_hosted=True, metric_prefix="example")

    ml.log(GaugeMetric("test_metric", 42, "Units"))
    ml.log(GaugeMetric("test_metric", 59, "Units", {"key1": "value1", "key2": "value2"}))
    ml.log(LLMTokensMetric("gpt-2", "inference", 1000))
    ml.log(LLMTokensMetric("gpt-2", "inference", 1000, tags={"key1": "value1", "key2": "value2"}))

    # Example of logging OpenAI completion metrics
    OPENAI_BASE_URL = "https://api.scaleway.ai/v1"
    openai_key = UserSecretsClient().get_secret("OPENAI_API_KEY")
    openai = OpenAI(base_url=OPENAI_BASE_URL, api_key=openai_key)
    completion = openai.chat.completions.create(model="llama-3.1-8b-instruct", messages=[{"role": "user", "content": "Hello"}])
    ml.log(OpenAICompletionMetric(completion))

    # Using the MetricLoggerCM context manager for automatic flushing
    with MetricLoggerCM(ml):
        ml.log(GaugeMetric("context_metric", 100, "Count"))
