# Storefront and commerce tools

The React application has addressable Home, Deal of the Day, Sales, Categories,
category, Recommendations, Cart and Order Lookup routes. FastAPI serves the app
on direct route loads. Client navigation retains the voice connection, cart and
conversation; browser back/forward changes the page without reconnecting voice.

## Product provenance

`sales_agent/data/catalog.json` is a curated snapshot of 24 real products, sourced
on September 24, 2026. Each item contains a manufacturer URL, checked date and
price kind. Prices are USD before tax. MacBook prices are launch references;
other entries are manufacturer page snapshots, not a live price feed. Sale
comparisons are only present where the source displayed both prices. Deal of the
Day is the store's featured pick, not a claim of a retailer's expiring promotion.

Source families: [Sony headphones](https://electronics.sony.com/audio/headphones/c/all-headphones),
[Sony monitors](https://electronics.sony.com/tv-video/gaming-monitors/c/inzone-monitors),
[Sony cameras](https://electronics.sony.com/imaging/compact-cameras/c/vlog-cameras),
[Google Pixel](https://store.google.com/config/pixel_9a?hl=en-US),
[Apple AirPods](https://www.apple.com/shop/buy-airpods/airpods-5),
[Apple iPad](https://www.apple.com/shop/buy-ipad/ipad),
[MacBook Air launch](https://www.apple.com/newsroom/2026/03/apple-introduces-the-new-macbook-air-with-m5/),
[Sonos Roam 2](https://www.sonos.com/en-us/shop/roam-2-olive).

Product graphics are explicitly labeled category illustrations, not product
photographs. Stock is synthetic (10 units per SKU); checkout places no real order.
The original fictional catalog is retained only as `simulation_catalog.json` for
reproducible HRL experiments. Those training results do not establish performance
with real customers or the new catalog.

## MCP integration

The app uses the official [MCP Python SDK v1](https://py.sdk.modelcontextprotocol.io/v1/),
pinned to `>=1.30,<2`. `commerce.py` launches `commerce_mcp.py` as a separate stdio
process and makes an actual MCP initialize/call-tool request. No extra port,
subscription, API key or merchant account is needed for this demo.

Only two tools exist, both read-only:

| Tool | Input | Result |
| --- | --- | --- |
| `inventory_lookup` | `product_id` (exact catalog SKU) | Synthetic quantity and demo/source flags |
| `order_lookup` | `order_id` | Public sample order status, or not found |

Try “Is Google Pixel 9a in stock?” or “Where is order DEMO-1001?” using voice or
text. Sample orders: DEMO-1001 shipped, DEMO-1002 processing, DEMO-1003 delivered.
The order page submits to the same agent command path. Responses are deterministic
tool results, including spoken confirmations; the LLM cannot choose an arbitrary
tool, invent a stock count, place an order or modify inventory. A 12-second timeout
returns an explicit unavailable response. OpenTelemetry spans record the tool name
and demo mode; application logs do not record order identifiers or tool contents.

This is a working local MCP integration, **not** a Shopify/WooCommerce integration.
There is no live merchant connection or remote MCP configuration yet. To connect a
real store, implement a provider behind these tools with merchant credentials held
server-side. Before exposing real orders, add customer authentication and enforce
ownership in the provider; an order number alone is not authorization. Do not
replace the public demo fixture with a database of real customer orders.

Run the server independently for an MCP host with this command from the app folder:

```sh
python -m sales_agent.commerce_mcp
```

## Checks

```sh
python -m unittest discover -s tests -v
node --test tests/voice-controller.test.cjs tests/cascade-controller.test.cjs
cd frontend
npm ci
npm run build
```

Tests include a real local MCP subprocess round trip, tool allowlisting, failure
handling, unknown orders, earphones after a speakers request, model-name prefix
disambiguation, server deep links, and persisted cart commands.
