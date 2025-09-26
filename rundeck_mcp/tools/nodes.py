"""Node management tools."""

from typing import Any

from ..client import get_client
from ..models.base import ListResponseModel
from ..models.rundeck import Node, NodeDetails, NodeSummary


def get_nodes(
    project: str, filter_query: str | None = None, tags: str | None = None, server: str | None = None
) -> ListResponseModel[Node]:
    """Get nodes from a project with optional filtering.

    Args:
        project: Project name
        filter_query: Rundeck node filter query (optional). Examples:
                     - "name: Server-1-infra" (exact name)
                     - ".*Windows.*" (regex pattern)
                     - "osFamily: windows" (Windows nodes)
                     - "hostname: 192.168.1.100" (by IP)
        tags: Tags filter (optional, e.g., "windows,production")
        server: Server name to query (optional)

    Returns:
        List of nodes with their attributes, hostnames, and OS details
        Use this to find exact node names for adhoc commands
    """
    client = get_client(server)
    params = {}
    if filter_query:
        params["filter"] = filter_query
    if tags:
        params["tags"] = tags

    response = client._make_request("GET", f"project/{project}/resources", params=params)

    nodes = []
    for node_data in response:
        nodes.append(
            Node(
                name=node_data["nodename"],
                hostname=node_data.get("hostname", ""),
                os_name=node_data.get("osName"),
                os_version=node_data.get("osVersion"),
                os_arch=node_data.get("osArch"),
                tags=node_data.get("tags", "").split(",") if node_data.get("tags") else [],
                attributes=node_data,
            )
        )

    return ListResponseModel[Node](response=nodes, total_count=len(nodes))


def get_node_details(project: str, node_name: str, server: str | None = None) -> NodeDetails:
    """Get detailed information about a specific node.

    Args:
        project: Project name
        node_name: Node name
        server: Server name to query (optional)

    Returns:
        Detailed node information
    """
    client = get_client(server)
    response = client._make_request("GET", f"project/{project}/resource/{node_name}")

    return NodeDetails(
        name=response["nodename"],
        hostname=response.get("hostname", ""),
        os_name=response.get("osName"),
        os_version=response.get("osVersion"),
        os_arch=response.get("osArch"),
        description=response.get("description"),
        tags=response.get("tags", "").split(",") if response.get("tags") else [],
        attributes=response,
        status=response.get("status"),
    )


def get_node_summary(project: str, server: str | None = None) -> NodeSummary:
    """Get statistical summary of nodes in a project.

    Args:
        project: Project name
        server: Server name to query (optional)

    Returns:
        Node summary statistics
    """
    nodes_response = get_nodes(project, server=server)
    nodes = nodes_response.response

    # Calculate statistics
    total_nodes = len(nodes)

    # OS distribution
    os_distribution = {}
    for node in nodes:
        os_key = node.os_name or "Unknown"
        os_distribution[os_key] = os_distribution.get(os_key, 0) + 1

    # Status breakdown (if available)
    status_breakdown = {}
    for node in nodes:
        status = node.attributes.get("status", "Unknown")
        status_breakdown[status] = status_breakdown.get(status, 0) + 1

    # Common tags
    tag_counts = {}
    for node in nodes:
        for tag in node.tags:
            if tag.strip():  # Skip empty tags
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # Get top 10 most common tags
    common_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    common_tags = [tag for tag, count in common_tags]

    return NodeSummary(
        total_nodes=total_nodes,
        os_distribution=os_distribution,
        status_breakdown=status_breakdown,
        common_tags=common_tags,
    )


def suggest_node_filters(
    project: str, search_term: str = "", server: str | None = None
) -> dict[str, Any]:
    """Suggest node filter patterns based on available nodes.

    Args:
        project: Project name
        search_term: Optional search term to find matching nodes (optional)
        server: Server name to query (optional)

    Returns:
        Dictionary with suggested filter patterns for nodes
    """
    # Get all nodes
    nodes_result = get_nodes(project, server=server)
    nodes = nodes_result.response

    if not nodes:
        return {
            "error": f"No nodes found in project '{project}'",
            "suggestion": "Check if the project exists and has nodes configured"
        }

    suggestions = {
        "total_nodes": len(nodes),
        "filter_examples": {},
        "matching_nodes": []
    }

    # If search term provided, find matching nodes
    if search_term:
        search_lower = search_term.lower()
        matching = []
        for node in nodes:
            if (search_lower in node.name.lower() or
                search_lower in node.hostname.lower() or
                search_lower in (node.os_name or "").lower()):
                matching.append({
                    "name": node.name,
                    "hostname": node.hostname,
                    "os": f"{node.os_name} ({node.os_family})",
                    "exact_filter": f"name: {node.name}",
                    "hostname_filter": f"hostname: {node.hostname}",
                    "regex_filter": f".*{node.name.split('-')[0]}.*" if '-' in node.name else f".*{node.name[:5]}.*"
                })
        suggestions["matching_nodes"] = matching

    # Generate filter examples by category
    if nodes:
        # By name examples
        example_names = [n.name for n in nodes[:3]]
        suggestions["filter_examples"]["by_exact_name"] = [f"name: {name}" for name in example_names]

        # By regex examples
        suggestions["filter_examples"]["by_regex_pattern"] = [
            f".*{name.split('-')[0]}.*" if '-' in name else f".*{name[:4]}.*" for name in example_names[:2]
        ]

        # By OS examples
        os_families = list(set(n.os_family for n in nodes if n.os_family))
        suggestions["filter_examples"]["by_os_family"] = [f"osFamily: {os}" for os in os_families[:3]]

        # By hostname examples (if different from name)
        hostname_examples = [f"hostname: {n.hostname}" for n in nodes[:2] if n.hostname != n.name]
        if hostname_examples:
            suggestions["filter_examples"]["by_hostname"] = hostname_examples

    return suggestions


# Tool definitions
node_tools = {
    "read": [
        get_nodes,
        get_node_details,
        get_node_summary,
        suggest_node_filters,
    ],
    "write": [],
}
