"""Standalone read-only MCP server. All inventory and orders are demo fixtures.

Run with: python -m sales_agent.commerce_mcp (stdio transport).
No customer records, addresses, payment data, or write tools are exposed.
"""
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from .catalog import BY_ID

mcp = FastMCP('CircuitWise demo commerce')
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
DEMO_ORDERS = {
    'DEMO-1001': {'status': 'shipped', 'items': [{'product_id': 'google-pixel-9a', 'quantity': 1}]},
    'DEMO-1002': {'status': 'processing', 'items': [{'product_id': 'sony-wh1000xm5', 'quantity': 1}]},
    'DEMO-1003': {'status': 'delivered', 'items': [{'product_id': 'sonos-roam-2', 'quantity': 1}]},
}

@mcp.tool(annotations=READ_ONLY)
def inventory_lookup(product_id: str) -> dict:
    """Read synthetic stock for one exact catalog SKU; never real retailer stock."""
    product = BY_ID.get(product_id)
    return {'demo': True, 'product_id': product_id, 'found': product is not None,
            'quantity': product['stock'] if product else 0, 'source': 'local_demo'}

@mcp.tool(annotations=READ_ONLY)
def order_lookup(order_id: str) -> dict:
    """Read a public synthetic order fixture, DEMO-1001 through DEMO-1003."""
    order_id = order_id.upper()
    order = DEMO_ORDERS.get(order_id)
    return {'demo': True, 'order_id': order_id, 'found': order is not None,
            'status': order['status'] if order else 'not_found', 'source': 'local_demo'}

if __name__ == '__main__':
    mcp.run(transport='stdio')
