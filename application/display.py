from abc import ABC, abstractmethod


class Display(ABC):

    @abstractmethod
    def assistant_says(self, message):
        pass

    @abstractmethod
    def tool_about_to_execute(self, parsed_tool):
        pass

    @abstractmethod
    def tool_result(self, result):
        pass

    @abstractmethod
    def input(self) -> str:
        pass

    @abstractmethod
    def exit(self):
        pass
