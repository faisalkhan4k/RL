"""Allowlisted MCP client shared by voice and text; failures never invent facts."""
import asyncio
import json
import re
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from .catalog import BY_ID
from .commands import named_products
from .hrl.state import new_belief
from .telemetry import logger, tracer

async def call_tool(name, arguments):
    if name not in {'inventory_lookup', 'order_lookup'}:
        raise ValueError('Tool is not allowed')
    params = StdioServerParameters(command=sys.executable,
        args=['-m', 'sales_agent.commerce_mcp'], cwd=str(Path(__file__).parents[1]))
    with tracer.start_as_current_span('commerce.mcp') as span:
        span.set_attribute('mcp.tool.name', name)
        span.set_attribute('commerce.mode', 'local_demo')
        try:
            async with asyncio.timeout(12):
                async with stdio_client(params) as (read, write):
                    async with ClientSession(read, write) as client:
                        await client.initialize()
                        result = await client.call_tool(name, arguments)
                        if result.isError:
                            raise RuntimeError('Commerce tool failed')
                        data = result.structuredContent
                        if data is None:
                            data = json.loads(next(c.text for c in result.content if c.type == 'text'))
                        if data.get('demo') is not True or data.get('source') != 'local_demo':
                            raise ValueError('Unexpected commerce result')
                        return data
        except Exception:
            logger.warning('commerce.lookup_failed', extra={'fields': {'tool': name}})
            raise

def tool_result(reply, state):
    return {'reply': reply, 'tool_reply': reply, 'products': [BY_ID[i] for i in state.get('result_ids', []) if i in BY_ID],
            'actions': [], 'requirements': state['requirements'], 'belief': state.get('belief') or new_belief(),
            'cart': state['cart'], 'focus_product_id': None, 'strategy': 'CUSTOMER_COMMAND',
            'prediction': {'probability': None}, 'debug': {'executed_action': 'CUSTOMER_COMMAND',
            'language_source': 'mcp_tool_result', 'commerce_mode': 'local_demo'}}

async def commerce_command(text, state):
    order = re.search(r'\b(?:order\s+(?:demo|status)|(?:where|track|check|find|lookup|look up).{0,30}(?:order|delivery|shipment)|(?:delivery|shipment|tracking)\s+status)\b', text, re.I)
    inventory = re.search(r'\b(stock|inventory|availability|available)\b', text, re.I)
    if re.search(r'\b(add|put|remove|delete)\b', text, re.I):
        return None
    if not order and not inventory:
        return None
    try:
        if order:
            match = re.search(r'\bdemo[\s-]*(\d{4})\b', text, re.I)
            if not match:
                reply = 'This is a demo order system. Try “where is order DEMO-1001?” No real orders are connected.'
            else:
                data = await call_tool('order_lookup', {'order_id': f'DEMO-{match[1]}'})
                reply = f'Demo order {data["order_id"]} is {data["status"]}.' if data['found'] else 'That demo order was not found. Try DEMO-1001, DEMO-1002, or DEMO-1003.'
        else:
            targets = named_products(text)
            if not targets and re.search(r'\b(it|that|this)\b', text, re.I) and state.get('focused_product') in BY_ID:
                targets = [BY_ID[state['focused_product']]]
            if len(targets) != 1:
                reply = 'Which exact product should I check? The connected inventory is demo data, not retailer availability.'
            else:
                product = targets[0]
                data = await call_tool('inventory_lookup', {'product_id': product['id']})
                reply = f'The demo inventory has {data["quantity"]} units of {product["name"]}. This is simulated stock, not live retailer availability.'
    except Exception:
        reply = 'The inventory and order tool is unavailable right now. I cannot confirm that information. Please try again.'
    return tool_result(reply, state)
