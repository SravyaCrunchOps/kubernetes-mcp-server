"""
MCP Server for Kubernetes Usage using FastMCP
Supports 5 core Kubernetes APIs
"""

import argparse
import aiohttp
import ssl
import certifi
import json
import logging
import os
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP
import uvicorn

load_dotenv()

K8_BASE_URL = os.getenv("K8_BASE_URL")
K8_TOKEN = os.getenv("K8_TOKEN")
CA_CERT_PATH = os.path.join(os.path.dirname(__file__), os.getenv("CA_CERT_PATH"))

# configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("k8s-mcp-server")


# Initialize MCP Server
mcp = FastMCP("Kubernetes-mcp-server")


# mcp server configuration starts
# kubernetes server class
class K8sServer:
    """ Kubernetes Server"""
    def __init__(self):
        self.base_url = K8_BASE_URL.rstrip('/')
        self.token = K8_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    async def make_request(self, endpoint: str) -> dict:
        """ Make url request to Kuberenetes API """
        url = f"{self.base_url}/{endpoint}"
        # setup ssl context
        ssl_context = ssl.create_default_context()
        # Load the CA certificate
        try:
            ssl_context.load_verify_locations(CA_CERT_PATH)
            logger.info(f"Successfully loaded CA cert from: {CA_CERT_PATH}")
        except Exception as e:
            logger.error(f"Warning: Failed to load CA cert: {e}")
            ssl_context.load_verify_locations(certifi.where())
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=ssl_context)
        ) as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("Response data: %s", json.dumps(data, indent=2))
                    return data
                else:
                    logger.error(f"Error response: {response.status}")
                    return {"error": f"HTTP {response.status}"}


# initialize server
k8s = K8sServer()

# tool call-1: List all namespaces
@mcp.tool(
    name="list_all_namespaces",     # Custom tool name for the LLM
    description="Give list of all namespaces available in kubernetes cluster.", # Custom description
)
async def list_all_namespaces() -> list[dict]:
    """ List all Kubernetes Namespaces """
    try:        
        endpoint = "api/v1/namespaces"
        response = await k8s.make_request(endpoint)
        if isinstance(response, str):
            response = json.loads(response)

        list_of_namespaces = [{
            "name": ns["metadata"]["name"], 
            "createdAt": ns["metadata"]["creationTimestamp"],
            "status": ns["status"]["phase"]
        } for ns in response["items"]]
        return list_of_namespaces
        
    except Exception as e:
        print(f"Error: {e}")
        return [{"error": str(e)}]
    

# tool call-2: list of pods
@mcp.tool(
    name="list_all_pods_on_default",    
    description="Give list of all pods on default that is available in kubernetes cluster.", 
)
async def list_all_pods_on_default() -> list[dict]:
    """ List all PODS on default namespace """
    try:
        endpoint = "api/v1/namespaces/default/pods"
        response = await k8s.make_request(endpoint)
        if isinstance(response, str):
            response = json.loads(response)
        
        list_of_pods = [{
            "name": pod["metadata"]["name"],
            "createdAt": pod["metadata"]["creationTimestamp"],
            "status": pod["status"]["phase"]
        } for pod in response["items"]]
        return list_of_pods

    except Exception as e:
        print(f"Error: {e}")
        return [{"error": str(e)}]


# tool call-3: list of services
@mcp.tool(
    name="list_all_services_on_default",    
    description="Give list of all services on default that is available in kubernetes cluster.", 
)
async def list_all_services_on_default() -> list[dict]:
    """ List all Services on default namespace """
    try:
        endpoint = "api/v1/namespaces/default/services"
        response = await k8s.make_request(endpoint)
        if isinstance(response, str):
            response = json.loads(response)
        
        list_of_services = [{
            "name": service["metadata"]["name"],
            "createdAt": service["metadata"]["creationTimestamp"],
            "port": [{ p["name"]: f'protocol: {p["protocol"]} port: {p["port"]} targetPort: {p["targetPort"]}' } for p in service["spec"]["ports"]],
            "clusterIP": service["spec"]["clusterIP"]
        } for service in response["items"]]
        print(list_of_services)
        return list_of_services

    except Exception as e:
        print(f"Error: {e}")
        return [{"error": str(e)}]


# tool call-4: list of loki deployments
@mcp.tool(
    name="list_all_deployments_on_loki",    
    description="Give list of all deployments on loki that is available in kubernetes cluster.", 
)
async def list_all_deployments_on_loki() -> list[dict]:
    """ List all Deployments on loki namespace """
    try:
        endpoint = "apis/apps/v1/namespaces/loki/deployments"
        response = await k8s.make_request(endpoint)
        if isinstance(response, str):
            response = json.loads(response)
            
        list_of_deployments = [{
            "name": deployment["metadata"]["name"],
            "createdAt": deployment["metadata"]["creationTimestamp"],
        } for deployment in response["items"]]
        return list_of_deployments

    except Exception as e:
        print(f"Error: {e}")
        return [{"error": str(e)}]


# list of loki configmaps
@mcp.tool(
    name="list_all_configmaps_on_loki",    
    description="Give list of all configmaps on loki that is available in kubernetes cluster.", 
)
async def list_all_configmaps_on_loki() -> list[dict]:
    """ List all ConfigMaps on loki namespace """
    try:
        endpoint = "api/v1/namespaces/loki/configmaps"
        response = await k8s.make_request(endpoint)
        if isinstance(response, str):
            response = json.loads(response)

        list_of_configmaps = [{
            "name": configmap["metadata"]["name"],
            "createdAt": configmap["metadata"]["creationTimestamp"],
        } for configmap in response["items"]]
        return list_of_configmaps

    except Exception as e:
        print(f"Error: {e}")
        return [{"error": str(e)}]


if __name__ == "__main__":
    print("Running in STDIO mode")
    mcp.run(transport='stdio')
