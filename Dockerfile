# =========================================================================
# Sovereign AgentOps — Community Edition
# Minimal MCP server demo image
# =========================================================================
# This image runs the stdio-based MCP server with zero external
# dependencies.  It is intended for evaluation, CI pipelines, and
# local experimentation.
#
# Build:
#   docker build -t agentops-community -f Dockerfile ..
#
# Run (stdio):
#   echo '{"jsonrpc":"2.0","id":1,"method":"list_tools"}' \
#     | docker run -i --rm agentops-community
#
# Run (with compose, recommended):
#   docker compose up
# =========================================================================

FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered I/O
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEMO_MODE=true \
    WORKSPACE_ROOT=/workspace

# Create the workspace directory and a sample file for policy inspection
RUN mkdir -p /workspace/examples && \
    echo "Hello from Sovereign AgentOps!" > /workspace/examples/hello.txt

# Copy the MCP server (stdlib only — no pip install needed)
COPY tools/ /app/tools/

# Set the working directory
WORKDIR /app

# The MCP server speaks JSON-RPC over stdio
CMD ["python3", "tools/mcp-server.py"]
