#!/usr/bin/env python3
"""
Jenkins MCP Server - Control Jenkins through Claude via MCP
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Union
import httpx
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import NotificationOptions
from urllib.parse import urljoin, quote
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jenkins-mcp-server")

class JenkinsClient:
    def __init__(self, base_url: str, username: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.auth = base64.b64encode(f"{username}:{api_token}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {self.auth}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to Jenkins API"""
        url = urljoin(self.base_url, endpoint)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    timeout=30.0,
                    **kwargs
                )
                response.raise_for_status()
                
                # Handle different content types
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    return response.json()
                else:
                    return {"content": response.text, "status_code": response.status_code}
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise Exception(f"Jenkins API error: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
                raise Exception(f"Failed to connect to Jenkins: {str(e)}")

    async def get_jobs(self) -> List[Dict[str, Any]]:
        """Get list of all jobs"""
        data = await self._make_request("GET", "/api/json?tree=jobs[name,url,color,lastBuild[number,timestamp,result]]")
        return data.get('jobs', [])
    
    async def get_job_info(self, job_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific job"""
        endpoint = f"/job/{quote(job_name)}/api/json"
        return await self._make_request("GET", endpoint)
    
    async def build_job(self, job_name: str, parameters: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Trigger a job build"""
        if parameters:
            endpoint = f"/job/{quote(job_name)}/buildWithParameters"
            return await self._make_request("POST", endpoint, data=parameters)
        else:
            endpoint = f"/job/{quote(job_name)}/build"
            return await self._make_request("POST", endpoint)
    
    async def get_build_info(self, job_name: str, build_number: int) -> Dict[str, Any]:
        """Get information about a specific build"""
        endpoint = f"/job/{quote(job_name)}/{build_number}/api/json"
        return await self._make_request("GET", endpoint)
    
    async def get_build_console(self, job_name: str, build_number: int) -> str:
        """Get console output for a build"""
        endpoint = f"/job/{quote(job_name)}/{build_number}/consoleText"
        result = await self._make_request("GET", endpoint)
        return result.get('content', '')
    
    async def stop_build(self, job_name: str, build_number: int) -> Dict[str, Any]:
        """Stop a running build"""
        endpoint = f"/job/{quote(job_name)}/{build_number}/stop"
        return await self._make_request("POST", endpoint)
    
    async def get_queue(self) -> List[Dict[str, Any]]:
        """Get build queue"""
        data = await self._make_request("GET", "/queue/api/json")
        return data.get('items', [])
    
    async def get_nodes(self) -> List[Dict[str, Any]]:
        """Get Jenkins nodes/agents"""
        data = await self._make_request("GET", "/computer/api/json")
        return data.get('computer', [])

# Initialize Jenkins client
jenkins_client = None

def init_jenkins_client():
    global jenkins_client
    jenkins_url = os.getenv('JENKINS_URL')
    jenkins_username = os.getenv('JENKINS_USERNAME')
    jenkins_token = os.getenv('JENKINS_API_TOKEN')
    
    if not all([jenkins_url, jenkins_username, jenkins_token]):
        raise ValueError("Missing Jenkins configuration. Please set JENKINS_URL, JENKINS_USERNAME, and JENKINS_API_TOKEN environment variables.")
    
    jenkins_client = JenkinsClient(jenkins_url, jenkins_username, jenkins_token)

# Create MCP server
server = Server("jenkins-controller")

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available Jenkins tools"""
    return [
        types.Tool(
            name="list_jobs",
            description="List all Jenkins jobs with their status",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="get_job_info",
            description="Get detailed information about a specific Jenkins job",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_name": {"type": "string", "description": "Name of the Jenkins job"}
                },
                "required": ["job_name"]
            }
        ),
        types.Tool(
            name="build_job",
            description="Trigger a Jenkins job build",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_name": {"type": "string", "description": "Name of the Jenkins job"},
                    "parameters": {
                        "type": "object",
                        "description": "Build parameters (optional)",
                        "additionalProperties": {"type": "string"}
                    }
                },
                "required": ["job_name"]
            }
        ),
        types.Tool(
            name="get_build_info",
            description="Get information about a specific build",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_name": {"type": "string", "description": "Name of the Jenkins job"},
                    "build_number": {"type": "integer", "description": "Build number"}
                },
                "required": ["job_name", "build_number"]
            }
        ),
        types.Tool(
            name="get_build_console",
            description="Get console output for a specific build",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_name": {"type": "string", "description": "Name of the Jenkins job"},
                    "build_number": {"type": "integer", "description": "Build number"}
                },
                "required": ["job_name", "build_number"]
            }
        ),
        types.Tool(
            name="stop_build",
            description="Stop a running build",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_name": {"type": "string", "description": "Name of the Jenkins job"},
                    "build_number": {"type": "integer", "description": "Build number"}
                },
                "required": ["job_name", "build_number"]
            }
        ),
        types.Tool(
            name="get_queue",
            description="Get the Jenkins build queue",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="get_nodes",
            description="Get Jenkins nodes/agents status",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls"""
    if jenkins_client is None:
        return [types.TextContent(
            type="text",
            text="Jenkins client not initialized. Please check your environment variables."
        )]
    
    try:
        if name == "list_jobs":
            jobs = await jenkins_client.get_jobs()
            result = "Jenkins Jobs:\n"
            for job in jobs:
                status = job.get('color', 'unknown')
                last_build = job.get('lastBuild')
                if last_build:
                    result += f"• {job['name']} - Status: {status} - Last Build: #{last_build.get('number', 'N/A')} ({last_build.get('result', 'Unknown')})\n"
                else:
                    result += f"• {job['name']} - Status: {status} - No builds yet\n"
            return [types.TextContent(type="text", text=result)]
        
        elif name == "get_job_info":
            job_name = arguments["job_name"]
            info = await jenkins_client.get_job_info(job_name)
            result = f"Job Information for '{job_name}':\n"
            result += f"Description: {info.get('description', 'N/A')}\n"
            result += f"URL: {info.get('url', 'N/A')}\n"
            result += f"Buildable: {info.get('buildable', 'N/A')}\n"
            result += f"Color: {info.get('color', 'N/A')}\n"
            
            last_build = info.get('lastBuild')
            if last_build:
                result += f"Last Build: #{last_build.get('number', 'N/A')}\n"
            
            return [types.TextContent(type="text", text=result)]
        
        elif name == "build_job":
            job_name = arguments["job_name"]
            parameters = arguments.get("parameters")
            await jenkins_client.build_job(job_name, parameters)
            result = f"Build triggered for job '{job_name}'"
            if parameters:
                result += f" with parameters: {parameters}"
            return [types.TextContent(type="text", text=result)]
        
        elif name == "get_build_info":
            job_name = arguments["job_name"]
            build_number = arguments["build_number"]
            info = await jenkins_client.get_build_info(job_name, build_number)
            
            result = f"Build Information for '{job_name}' #{build_number}:\n"
            result += f"Result: {info.get('result', 'N/A')}\n"
            result += f"Duration: {info.get('duration', 'N/A')}ms\n"
            result += f"Timestamp: {info.get('timestamp', 'N/A')}\n"
            result += f"Building: {info.get('building', 'N/A')}\n"
            result += f"URL: {info.get('url', 'N/A')}\n"
            
            return [types.TextContent(type="text", text=result)]
        
        elif name == "get_build_console":
            job_name = arguments["job_name"]
            build_number = arguments["build_number"]
            console_output = await jenkins_client.get_build_console(job_name, build_number)
            
            # Truncate if too long
            if len(console_output) > 5000:
                console_output = console_output[-5000:] + "\n\n[Output truncated - showing last 5000 characters]"
            
            return [types.TextContent(
                type="text", 
                text=f"Console output for '{job_name}' #{build_number}:\n\n{console_output}"
            )]
        
        elif name == "stop_build":
            job_name = arguments["job_name"]
            build_number = arguments["build_number"]
            await jenkins_client.stop_build(job_name, build_number)
            return [types.TextContent(
                type="text", 
                text=f"Stopped build #{build_number} for job '{job_name}'"
            )]
        
        elif name == "get_queue":
            queue = await jenkins_client.get_queue()
            if not queue:
                result = "Build queue is empty"
            else:
                result = "Build Queue:\n"
                for item in queue:
                    task = item.get('task', {})
                    result += f"• {task.get('name', 'Unknown')} - Waiting time: {item.get('inQueueSince', 'N/A')}\n"
            return [types.TextContent(type="text", text=result)]
        
        elif name == "get_nodes":
            nodes = await jenkins_client.get_nodes()
            result = "Jenkins Nodes:\n"
            for node in nodes:
                result += f"• {node.get('displayName', 'Unknown')} - Online: {not node.get('offline', True)}"
                if node.get('offline'):
                    result += f" (Reason: {node.get('offlineCauseReason', 'Unknown')})"
                result += "\n"
            return [types.TextContent(type="text", text=result)]
        
        else:
            return [types.TextContent(
                type="text", 
                text=f"Unknown tool: {name}"
            )]
            
    except Exception as e:
        logger.error(f"Error in {name}: {str(e)}")
        return [types.TextContent(
            type="text", 
            text=f"Error executing {name}: {str(e)}"
        )]

async def main():
    """Main function to run the MCP server"""
    try:
        init_jenkins_client()
        logger.info("Jenkins MCP Server started")
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="jenkins-controller",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    ),
                ),
            )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())