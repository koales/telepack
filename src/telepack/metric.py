# Copyright 2025 Koales Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from newrelic_telemetry_sdk import GaugeMetric, MetricClient
from .endpoints import METRIC_API_HOST_EU

__all__ = (
    "GaugeMetric",
    "LLMTokensMetric",
    "MetricLogger",
    "MetricLoggerCM",
    "OpenAICompletionMetric",
)

# Class to log metrics to New Relic
class MetricLogger(object):
    _license_key = None
    _api_host = None

    _client_service_name = None
    _client_host = None

    _metric_prefix = ""
    _metric_client = None
    _metric_batch = []
    _batch_send = True

    chars_to_replace_to_underscore = ["-", "/", ":", " "]

    _active = True
    
    def __init__(
        self,
        client_service_name=None,
        client_host=None,
        license_key=None,
        use_kaggle_secret=False,
        license_key_secret_name=None,
        early_init=True,
        eu_hosted=False,
        metric_prefix="",
        batch_send=True,
        ):
        if license_key is not None:
            self._license_key = license_key
        else:
            if use_kaggle_secret:
                # Import Kaggle Secrets if available, will raise an exception if not installed
                from kaggle_secrets import UserSecretsClient
                self._license_key = UserSecretsClient().get_secret(license_key_secret_name)
                
        if self._license_key is None or self._license_key == "":
            raise Exception("No license key provided, must provide license key directly or Kaggle secret name")
        
        if eu_hosted:
            self._api_host = METRIC_API_HOST_EU

        self._client_service_name = client_service_name
        self._client_host = client_host

        self._metric_prefix = metric_prefix
        self._batch_send = batch_send

        # Clear any previous batches
        self._metric_batch = []
        
        if early_init:
            self._init_client()

    def enable(self):
        self._active = True

    def disable(self):
        self._active = False

    def is_enabled(self):
        return self._active == True

    def flush(self):
        self._report_metric_batch()
    
    def _init_client(self):
        if self._metric_client is None:
            self._metric_client = MetricClient(self._license_key, host=self._api_host)
            
            # We don't need the license key anymore, so clear it
            self._license_key = None

    def common_attributes(self):
        common = {}
        
        if self._client_service_name is not None:
            common["service.name"] = self._client_service_name
        if self._client_host is not None:
            common["host"] = self._client_host
            
        return common

    def log(self, metric):
        # Do not log metrics if the logger is not active
        if not self.is_enabled():
            return

        metric['name'] = self.format_metric_name(metric['name'])

        # augment metric's custom attributes with common attributes
        metric['attributes'] = {**metric.get('attributes', {}), **self.common_attributes()}

        if self._batch_send:
            self._metric_batch.append(metric)
        else:
            self._store_single_metric(metric)
    
    def _store_single_metric(self, metric):
        self._init_client()
        response = self._metric_client.send(metric)
        response.raise_for_status()
    
    def _report_metric_batch(self):
        if len(self._metric_batch) == 0:
            # nothing to do, no metrics to send
            return
        
        self._init_client()
        response = self._metric_client.send_batch(self._metric_batch)
        response.raise_for_status()
        
        # reset the batch
        self._metric_batch = []

    def format_metric_name(self, metric_name, to_lower=True):
        # add the metric prefix
        if self._metric_prefix != "":
            metric_name = f"{self._metric_prefix}.{metric_name}"

        # replace any invalid characters in the metric name with underscores
        for char in self.chars_to_replace_to_underscore:
            metric_name = metric_name.replace(char, "_")
        
        if to_lower:
            metric_name = metric_name.lower()

        return metric_name

class GaugeMetric(GaugeMetric):
    def __init__(self, name, value, units, tags=None):
        # if tags is a dict, add units to it, otherwise create a new dict just with units
        if not isinstance(tags, dict):
            tags = {}
        tags["units"] = units
            
        super().__init__(name, value, tags=tags)

class LLMTokensMetric(GaugeMetric):
    def __init__(self, model, usage_type, tokens, name="llm_tokens", units="Tokens", tags=None):
        if not isinstance(tags, dict):
            tags = {}
        tags["model"] = model
        tags["usage"] = usage_type
        super().__init__(name, tokens, units, tags=tags)

class OpenAICompletionMetric(LLMTokensMetric):
    # Metric for OpenAI completions
    def __init__(self, completion, name="llm_tokens", units="Tokens", usage="Inference", tags=None):
        if not isinstance(tags, dict):
            tags = {}

        model = completion.model
        total_tokens = completion.usage.total_tokens

        tags["completion_tokens"] = completion.usage.completion_tokens
        tags["prompt_tokens"] = completion.usage.prompt_tokens

        tags["usage"] = usage

        super().__init__(model, usage, total_tokens, name, units, tags=tags)

class MetricLoggerCM():
    def __init__(self, logger):
        self._logger = logger

    def __enter__(self):
        return self._logger

    def __exit__(self, exc_type, exc_value, traceback):
        self._logger.flush()
