"""Node management tools."""

from ..client import get_client
from ..models.base import ListResponseModel
from ..models.rundeck import Node, NodeDetails, NodeSummary


def get_nodes(
    project: str, filter_query: str | None = None, tags: str | None = None, server: str | None = None
) -> ListResponseModel[Node]:
    """Get nodes from a project.

    Args:
        project: Project name
        filter_query: Rundeck node filter query (optional)
        tags: Tags filter (optional)
        server: Server name to query (optional)

    Returns:
        List of nodes
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


# Tool definitions
node_tools = {
    "read": [
        get_nodes,
        get_node_details,
        get_node_summary,
    ],
    "write": [],
}
