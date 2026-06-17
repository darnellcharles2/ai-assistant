async def placeholder_tool(step):
    return {'status': 'ok', 'detail': f"Executed {step['description']}"}

# Example tool registration (uncomment for use)
# executor = TaskExecutor()
# asyncio.run(executor.register_tool('execution', placeholder_tool))
