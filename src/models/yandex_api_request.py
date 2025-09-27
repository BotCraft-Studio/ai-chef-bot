# Класс, описывающий запрос к YandexAPI

class YandexAPIRequest:
    class CompletionOptions:
        def __init__(self,
                     stream: bool = False,
                     temperature: float = 0.6,
                     max_tokens: int = 1000,
                     reasoning_options: dict = None):
            self.stream = stream
            self.temperature = temperature
            self.max_tokens = max_tokens
            self.reasoning_options = reasoning_options

        def to_json(self):
            return {
                "stream": self.stream,
                "temperature": self.temperature,
                "maxTokens": self.max_tokens,
                "reasoningOptions": self.reasoning_options,
            }

    def __init__(self,
                 folder_id: str,
                 messages: list[dict],
                 completion_options: CompletionOptions):
        self.model_uri = f"gpt://{folder_id}/yandexgpt"
        self.completion_options = completion_options
        self.messages = messages

    def to_json(self):
        return {
            "model_uri": self.model_uri,
            "completion_options": self.completion_options.to_json(),
            "messages": self.messages,
        }
