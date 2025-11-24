const { ServiceBroker } = require("moleculer");

module.exports = {
    name: "math",

    actions: {
        add(ctx) {
            console.log(`[Node] math.add called with params:`, ctx.params);
            return Number(ctx.params.a) + Number(ctx.params.b);
        },

        subtract(ctx) {
            console.log(`[Node] math.subtract called with params:`, ctx.params);
            return Number(ctx.params.a) - Number(ctx.params.b);
        },

        multiply(ctx) {
            console.log(`[Node] math.multiply called with params:`, ctx.params);
            return Number(ctx.params.a) * Number(ctx.params.b);
        },

        divide(ctx) {
            console.log(`[Node] math.divide called with params:`, ctx.params);
            if (ctx.params.b === 0) {
                throw new Error("Division by zero");
            }
            return Number(ctx.params.a) / Number(ctx.params.b);
        }
    },

    events: {
        "test.**": {
            handler(ctx) {
                console.log(`[Node] Received event: ${ctx.eventName}`, ctx.params);
            }
        }
    },

    created() {
        console.log("[Node] Math service created");
    },

    started() {
        console.log("[Node] Math service started");

        // Emit a test event after startup
        setTimeout(() => {
            this.broker.broadcast("node.event", {
                message: "Hello from Node.js",
                timestamp: Date.now()
            });
        }, 2000);
    }
};
