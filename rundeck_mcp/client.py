"""Client management for Rundeck MCP Server."""

import logging
import os
from typing import Any
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models.rundeck import Server

logger = logging.getLogger(__name__)


class RundeckClient:
    """Client for interacting with Rundeck API."""

    def __init__(self, base_url: str, api_token: str, api_version: str = "47", name: str = "default"):
        """Initialize Rundeck client.

        Args:
            base_url: Rundeck server URL
            api_token: API authentication token
            api_version: API version to use
            name: Server identifier name
        """
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.api_version = api_version
        self.name = name

        # Configure session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set headers
        self.session.headers.update(
            {
                "X-Rundeck-Auth-Token": api_token,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": f"rundeck-mcp-server/1.0.0 (python-requests/{requests.__version__})",
            }
        )

        logger.info(f"Initialized Rundeck client for {self.name} (API v{self.api_version})")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> dict[str, Any]:
        """Make a request to the Rundeck API with enhanced error handling.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters

        Returns:
            JSON response data

        Raises:
            requests.exceptions.RequestException: On request failure
        """
        url = urljoin(f"{self.base_url}/api/{self.api_version}/", endpoint.lstrip("/"))

        # Add default timeout
        if "timeout" not in kwargs:
            kwargs["timeout"] = 30

        try:
            logger.debug(f"Making {method} request to {url}")
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()

            # Handle empty responses
            if not response.content.strip():
                return {}

            return response.json()

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for {self.name}: {e}")
            raise requests.exceptions.ConnectionError(
                f"Failed to connect to Rundeck server '{self.name}' at {self.base_url}. "
                f"Please check if the server is running and accessible."
            ) from e

        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error for {self.name}: {e}")
            raise requests.exceptions.Timeout(
                f"Request to Rundeck server '{self.name}' timed out. The server may be overloaded or unreachable."
            ) from e

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {self.name}: {e}")
            if e.response and e.response.status_code == 401:
                raise requests.exceptions.HTTPError(
                    f"Authentication failed for server '{self.name}'. Please check your API token."
                ) from e
            elif e.response and e.response.status_code == 403:
                raise requests.exceptions.HTTPError(
                    f"Access denied for server '{self.name}'. Please check your permissions."
                ) from e
            elif e.response and e.response.status_code == 404:
                raise requests.exceptions.HTTPError(
                    f"Resource not found on server '{self.name}'. Please check the endpoint or resource ID."
                ) from e
            else:
                raise requests.exceptions.HTTPError(
                    f"HTTP error {e.response.status_code if e.response else 'unknown'} for server '{self.name}': {e}"
                ) from e

    def get_system_info(self) -> dict[str, Any]:
        """Get system information."""
        return self._make_request("GET", "system/info")

    def health_check(self) -> bool:
        """Check if the server is healthy and accessible.

        Returns:
            True if server is healthy, False otherwise
        """
        try:
            self.get_system_info()
            return True
        except Exception as e:
            logger.warning(f"Health check failed for {self.name}: {e}")
            return False


class ClientManager:
    """Manages multiple Rundeck clients."""

    def __init__(self):
        """Initialize client manager."""
        self._clients: dict[str, RundeckClient] = {}
        self._primary_client: RundeckClient | None = None
        self._load_clients()

    def _load_clients(self) -> None:
        """Load clients from environment variables."""
        # Load primary client
        primary_url = os.getenv("RUNDECK_URL")
        primary_token = os.getenv("RUNDECK_API_TOKEN")

        if primary_url and primary_token:
            primary_name = os.getenv("RUNDECK_NAME", "primary")
            primary_version = os.getenv("RUNDECK_API_VERSION", "47")

            self._primary_client = RundeckClient(
                base_url=primary_url, api_token=primary_token, api_version=primary_version, name=primary_name
            )
            self._clients[primary_name] = self._primary_client
            logger.info(f"Loaded primary client: {primary_name}")

        # Load additional clients (numbered 1-9)
        for i in range(1, 10):
            url = os.getenv(f"RUNDECK_URL_{i}")
            token = os.getenv(f"RUNDECK_API_TOKEN_{i}")

            if url and token:
                name = os.getenv(f"RUNDECK_NAME_{i}", f"server_{i}")
                version = os.getenv(f"RUNDECK_API_VERSION_{i}", "47")

                client = RundeckClient(base_url=url, api_token=token, api_version=version, name=name)
                self._clients[name] = client
                logger.info(f"Loaded additional client: {name}")

    def get_client(self, server_name: str | None = None) -> RundeckClient:
        """Get a client by name or return primary client.

        Args:
            server_name: Server name to get client for

        Returns:
            RundeckClient instance

        Raises:
            ValueError: If no clients configured or server not found
        """
        if not self._clients:
            raise ValueError(
                "No Rundeck clients configured. Please set RUNDECK_URL and RUNDECK_API_TOKEN environment variables."
            )

        if server_name is None:
            if self._primary_client is None:
                # Return any available client if no primary
                return next(iter(self._clients.values()))
            return self._primary_client

        if server_name not in self._clients:
            available = list(self._clients.keys())
            raise ValueError(f"Server '{server_name}' not found. Available servers: {available}")

        return self._clients[server_name]

    def list_servers(self) -> list[Server]:
        """List all configured servers.

        Returns:
            List of server configurations
        """
        servers = []
        for name, client in self._clients.items():
            servers.append(
                Server(
                    name=name,
                    url=client.base_url,
                    api_version=client.api_version,
                    is_primary=(client == self._primary_client),
                )
            )
        return servers

    def health_check_all(self) -> dict[str, bool]:
        """Check health of all configured servers.

        Returns:
            Dictionary mapping server names to health status
        """
        health_status = {}
        for name, client in self._clients.items():
            health_status[name] = client.health_check()
        return health_status


# Global client manager instance
_client_manager: ClientManager | None = None


def get_client_manager() -> ClientManager:
    """Get the global client manager instance."""
    global _client_manager
    if _client_manager is None:
        _client_manager = ClientManager()
    return _client_manager


def get_client(server_name: str | None = None) -> RundeckClient:
    """Get a Rundeck client.

    Args:
        server_name: Server name to get client for

    Returns:
        RundeckClient instance
    """
    return get_client_manager().get_client(server_name)
