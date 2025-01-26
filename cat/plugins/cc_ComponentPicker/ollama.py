import requests
import json


class OllamaLLM:
    def __init__(self, api_url, model, logger=None, keep_alive="10m"):
        self.api_url = api_url
        self.model = model
        self.logger = logger
        self.keep_alive = keep_alive

        self._log("Initializing ollama model")
        model_downloaded = self._check_model()
        self._log(f"Model state: {model_downloaded}")
        if not model_downloaded:
            self._download_model()

    def _log(self, string, type=0):
        """type:
        - 0: info
        - 1: error
        """
        if not self.logger:
            return

        match type:
            case 0:
                self.logger.info(string)
            case _:
                self.logger.error(string)

    def _download_model(self):
        try:
            self._log(f"Starting download of model: {self.model}")

            response = requests.post(
                f"{self.api_url}/pull", json={"model": self.model}, stream=True
            )

            last_print = ""

            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line.decode("utf-8"))
                        actual_print = f"Status: {data.get('status')}"

                        if actual_print != last_print:
                            self._log(actual_print)

                        last_print = actual_print

                        if data.get("status") == "success":
                            self._log(f"Model {self.model} downloaded successfully.")
                            break
                        if data.get("status") == "downloading digestname":
                            self._log(
                                f"Downloading file: {data.get('digest')}, completed: {data.get('completed')} of {data.get('total')}"
                            )
            else:
                self._log(
                    f"Failed to start model download, code: {response.status_code}", 1
                )
                self._log(f"Response: {response.text}", 1)
        except Exception as e:
            self._log(f"Error downloading model: {e}", 1)

    def _check_model(self):
        try:
            response = requests.get(f"{self.api_url}/tags")

            if response.status_code == 200:
                models = response.json().get("models", [])

                for model in models:
                    if model["name"] == self.model:
                        return True
                return False
            else:
                self._log(f"Failed to get models list, code: {response.status_code}", 1)
                return False
        except Exception as e:
            self._log(f"Error checking model: {e}", 1)
            return False

    def load_model(self):
        request = {"model": self.model, "keep_alive": self.keep_alive}

        try:
            response = requests.post(f"{self.api_url}/generate", json=request)
            if response.status_code == 200:
                self._log(f"Model '{self.model}' loaded")
                return True
            else:
                self._log(
                    f"Failed to load model '{self.model}', code: {response.status_code}",
                    1,
                )
                self._log(f"Response: {response.text}", 1)
                return False
        except Exception as e:
            self._log(f"Error loading model '{self.model}': {e}", 1)
            return False

    def llm(self, query, format=None):
        request = {
            "model": self.model,
            "messages": [{"role": "user", "content": query}],
            "stream": False,
        }
        if format:
            request["format"] = format

        try:
            response = requests.post(f"{self.api_url}/chat", json=request)

            if response.status_code == 200:
                response_data = response.json()

                if "message" in response_data:
                    return response_data["message"]["content"]
                else:
                    self._log(f"Ollama API response error", 1)
                    return None
            else:
                self._log(
                    f"Ollama error, code: {response.status_code}",
                    1,
                )
                self._log(f"Response: {response.text}", 1)
                return None
        except Exception as e:
            self._log(f"Ollama llm error: {e}", 1)
            return None
