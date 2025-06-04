import asyncio
from mcp_agent.core.fastagent import FastAgent

# create the application
fast = FastAgent("K8 Agent")

@fast.agent(
    "k8_agent",
    "Give the response as per user-queries",
    servers=["mcp-server-k8"]
)
async def main():
    async with fast.run() as agent:
        await agent.interactive()

if __name__ == "__main__":
    asyncio.run(main())
