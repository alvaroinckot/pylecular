module.exports = {
    name: "node-greeter",

    actions: {
        hello(ctx) {
            const name = ctx.params.name || "World";
            console.log(`[Node] greeter.hello called for: ${name}`);
            return `Hello ${name} from Node.js!`;
        },

        welcome(ctx) {
            console.log(`[Node] greeter.welcome called`);
            return {
                message: "Welcome from Node.js!",
                timestamp: Date.now(),
                nodeId: this.broker.nodeID
            };
        },

        echo(ctx) {
            console.log(`[Node] greeter.echo called with:`, ctx.params);
            return ctx.params;
        }
    },

    events: {
        "user.created": {
            handler(ctx) {
                console.log(`[Node] User created event received:`, ctx.params);
            }
        }
    },

    started() {
        console.log("[Node] Greeter service started");
    }
};
