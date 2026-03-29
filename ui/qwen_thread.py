"""
QwenThread - поток для генерации ответов Qwen без блокировки UI (стрим + отмена).
"""

import threading

from PyQt6.QtCore import QThread, pyqtSignal


class QwenThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    cancelled = pyqtSignal(str)

    def __init__(
        self,
        qwen_provider,
        user_prompt: str,
        system_prompt: str,
        cancel_event: threading.Event,
    ):
        super().__init__()
        self.qwen_provider = qwen_provider
        self.user_prompt = user_prompt
        self.system_prompt = system_prompt
        self.cancel_event = cancel_event

    def run(self):
        try:
            outcome, text = self.qwen_provider.generate_response_chat_stream(
                self.user_prompt,
                self.system_prompt,
                self.cancel_event,
            )
            if outcome == "ok":
                if text:
                    self.finished.emit(text)
                else:
                    self.error.emit("empty")
            elif outcome == "cancelled":
                self.cancelled.emit(text)
            else:
                self.error.emit("error")
        except Exception as e:
            self.error.emit(str(e))
