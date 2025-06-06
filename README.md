# MediaWiki MCP Server

A powerful Model Context Protocol (MCP) server that provides seamless integration between AI systems and MediaWiki instances. This server enables LLMs and automation tools to read, search, and edit wiki content through a standardized interface.

## 🚀 Features

- **Full Page Access**: Retrieve complete wiki page content without chunking
- **Content Management**: Create, edit, and update wiki pages programmatically  
- **Search Capabilities**: Search pages by title keywords
- **Version History**: Access page revision history
- **Docker Support**: Containerized deployment with auto-restart capabilities
- **VS Code Integration**: Works seamlessly with VS Code's MCP extension
- **Authentication**: Bot account support for secure API access

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Reference](#-api-reference)
- [Development](#-development)
- [Docker Deployment](#-docker-deployment)
- [VS Code Integration](#-vs-code-integration)
- [Contributing](#-contributing)

## ⚡ Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd mcp-mediawiki
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your MediaWiki credentials
   ```

3. **Run with Docker** (recommended):
   ```bash
   docker-compose up --build
   ```

4. **Or run locally**:
   ```bash
   pip install -r requirements.txt
   python mcp_mediawiki.py
   ```

5. **Test the server**:
   ```bash
   curl http://localhost:3000/
   ```

## 📦 Installation

### Prerequisites

- Python 3.12+
- Docker (optional but recommended)
- Access to a MediaWiki instance

### Local Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
```

### Docker Installation

```bash
# Build and run with Docker Compose
docker-compose up --build -d
```

## ⚙️ Configuration

Create a `.env` file in the project root with your MediaWiki instance details:

```env
# MediaWiki API Configuration
MW_API_HOST=wiki.example.com
MW_API_PATH=/wiki/
MW_USE_HTTPS=true

# Bot Account Credentials (optional but recommended)
MW_BOT_USER=mcp-bot
MW_BOT_PASS=secret-password

# Server Configuration
PORT=3000
HOST=0.0.0.0
```

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MW_API_HOST` | MediaWiki hostname | - | ✅ |
| `MW_API_PATH` | MediaWiki API path | `/wiki/` | ❌ |
| `MW_USE_HTTPS` | Use HTTPS for connections | `true` | ❌ |
| `MW_BOT_USER` | Bot account username | - | ❌ |
| `MW_BOT_PASS` | Bot account password | - | ❌ |
| `PORT` | Server port | `3000` | ❌ |
| `HOST` | Server host | `0.0.0.0` | ❌ |

### MediaWiki Bot Setup

For write operations, it's recommended to create a bot account with appropriate permissions:

```php
# Add to LocalSettings.php
$wgGroupPermissions['bot']['edit'] = true;
$wgGroupPermissions['bot']['createpage'] = true;
$wgGroupPermissions['bot']['writeapi'] = true;
```

## 🎯 Usage

### Health Check

Test if the server is running:

```bash
curl http://localhost:3000/
```

Expected response:
```json
{
  "status": "healthy",
  "service": "mcp-mediawiki",
  "version": "1.0.0"
}
```

### MCP Integration

The server provides an MCP transport at `/mcp` for integration with MCP-compatible clients like VS Code extensions or AI assistants.

## 📚 API Reference

### Resources

#### `wiki://{title}`

Retrieves the complete content of a wiki page.

**Example Request:**
```
GET wiki://DevOps
```

**Example Response:**
```json
{
  "@id": "wiki://DevOps",
  "@type": "Document", 
  "name": "DevOps",
  "content": "Full wikitext content...",
  "metadata": {
    "url": "https://wiki.example.com/wiki/DevOps",
    "last_modified": "2025-06-06T14:20:00Z",
    "namespace": 0,
    "length": 5032,
    "protection": {},
    "categories": []
  }
}
```

### Tools

#### `get_page`

Retrieve the full content and metadata of a specific wiki page.

**Parameters:**
- `title` (string): The title of the wiki page

#### `update_page`

Create or edit a wiki page with new content.

**Parameters:**
- `title` (string): The title of the wiki page
- `content` (string): The new content for the page
- `summary` (string): Edit summary describing the changes

**Example:**
```json
{
  "title": "DevOps",
  "content": "== Updated Section ==\nNew content here...",
  "summary": "Updated DevOps documentation"
}
```

#### `search_pages`

Search for pages by title keywords.

**Parameters:**
- `query` (string): Search query
- `limit` (integer, optional): Maximum number of results (default: 5)

#### `get_page_history`

Retrieve the revision history of a wiki page.

**Parameters:**
- `title` (string): The title of the wiki page
- `limit` (integer, optional): Maximum number of revisions (default: 5)

#### `server_status`

Get basic server configuration and MediaWiki version information.

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

The project includes a `docker-compose.yml` file for easy deployment:

```yaml
services:
  mcp-mediawiki:
    image: mcp-mediawiki:latest
    build: .
    restart: unless-stopped
    ports:
      - "3000:8000"
    env_file:
      - .env
    environment:
      - PYTHONUNBUFFERED=1
    networks:
      mcp_network:
        ipv4_address: 192.168.170.2

networks:
  mcp_network:
    driver: bridge
    ipam:
      driver: default
      config:
        - subnet: 192.168.170.0/24
          gateway: 192.168.170.1
```

**Start the service:**
```bash
docker-compose up -d --build
```

**View logs:**
```bash
docker-compose logs -f mcp-mediawiki
```

**Stop the service:**
```bash
docker-compose down
```

### Manual Docker Build

```bash
# Build the image
docker build -t mcp-mediawiki .

# Run the container
docker run -d \
  --name mcp-mediawiki \
  --restart unless-stopped \
  -p 3000:8000 \
  --env-file .env \
  mcp-mediawiki
```

## 🛠️ Development

### Project Structure

```
mcp-mediawiki/
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile             # Docker image definition
├── entrypoint.sh          # Container entrypoint script
├── mcp_mediawiki.py       # Main server implementation
├── requirements.txt       # Python dependencies
├── settings.json          # MCP server settings
├── .env.example          # Environment variables template
├── tests/                # Test files
│   └── test_server.py
├── Makefile              # Development commands
├── README.md             # This file
├── Usage.md              # Detailed usage documentation
└── LICENSE               # License file
```

### Local Development Setup

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd mcp-mediawiki
   cp .env.example .env
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run in development mode:**
   ```bash
   python mcp_mediawiki.py
   ```

4. **Run tests:**
   ```bash
   python -m pytest tests/
   ```

### Making Changes

1. **Code formatting:**
   ```bash
   black mcp_mediawiki.py
   ```

2. **Linting:**
   ```bash
   flake8 mcp_mediawiki.py
   ```

3. **Type checking:**
   ```bash
   mypy mcp_mediawiki.py
   ```

### Available Make Commands

```bash
make build          # Build Docker image
make run            # Run with Docker Compose
make stop           # Stop Docker containers
make logs           # View container logs
make test           # Run tests
make clean          # Clean up Docker resources
```

## 🔧 VS Code Integration

### Setup in VS Code

1. **Install the MCP extension** in VS Code
2. **Add to your VS Code settings** (`settings.json`):

```json
{
  "mcp.servers": {
    "mediawiki": {
      "command": "python",
      "args": ["path/to/mcp-mediawiki/mcp_mediawiki.py"],
      "env": {
        "MW_API_HOST": "your-wiki-host.com",
        "MW_API_PATH": "/wiki/",
        "MW_USE_HTTPS": "true"
      }
    }
  }
}
```

3. **Or use the Docker version:**

```json
{
  "mcp.servers": {
    "mediawiki": {
      "transport": {
        "type": "http",
        "url": "http://localhost:3000/mcp"
      }
    }
  }
}
```

### Usage in VS Code

Once configured, you can:

- Ask the AI assistant to "Get the DevOps wiki page"
- Request edits like "Update the API documentation page with new examples"
- Search for pages: "Find all pages related to deployment"

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Ensure all tests pass: `make test`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to your branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Report bugs or request features on [GitHub Issues](issues)
- **Documentation**: Check [Usage.md](Usage.md) for detailed examples
- **Wiki**: Visit the project wiki for additional documentation

## 🙏 Acknowledgments

- [MCP Python SDK](https://pypi.org/project/mcp/) for the protocol implementation
- [mwclient](https://github.com/mwclient/mwclient) for MediaWiki API integration
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework

---

**Made with ❤️ for the AI and MediaWiki communities**
