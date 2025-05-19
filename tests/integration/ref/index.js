const { ServiceBroker } = require("moleculer");

// Create a broker
const broker = new ServiceBroker(
    {
        nodeID: "integration-1",
        transporter: "nats://localhost:4222",
    }
);

// Create a service
broker.createService({
    name: "math",
    actions: {
        add(ctx) {
            console.log("meta: " + JSON.stringify(ctx.meta))
            return Number(ctx.params.a) + Number(ctx.params.b);
        }
    },
    events: {
        seen(ctx) {
            ctx.logger.info("seen")
        },
        "test.abc.foo": {
            handler: () => {}
        }
    }
});

// Start broker
broker.start()
    // Call service
    .then(() => broker.call("math.add", { a: 5, b: 3 }))
    .then(res => console.log("5 + 3 =", res))
    .catch(err => console.error(`Error occurred! ${err.message}`));