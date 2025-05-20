import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # import pylecular
import numpy as np
from sklearn.linear_model import LinearRegression  # require scikit-learn

from pylecular.broker import Broker
from pylecular.context import Context
from pylecular.decorators import action
from pylecular.service import Service


class MLService(Service):
    name = "ml"

    def __init__(self):
        super().__init__(self.name)
        X = np.array([[1], [2], [3], [4]])
        y = np.array([2, 4, 6, 8])
        self.model = LinearRegression()
        self.model.fit(X, y)

    @action(params=["x"])
    async def predict(self, ctx: Context):
        x = float(ctx.params.get("x"))
        prediction = self.model.predict([[x]])
        return float(prediction[0])


# Example usage
import asyncio


async def main():
    broker = Broker("broker1")

    broker.register(MLService())

    await broker.start()

    res = await broker.call("ml.predict", {"x": 4})

    broker.logger.info(f"ml predicted {res}")


asyncio.run(main())
