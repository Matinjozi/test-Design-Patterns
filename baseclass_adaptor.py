from abc import ABC, abstractmethod

class RideAdapter(ABC):
    @abstractmethod
    async def adapt(self, response_json):
        pass