# Simple CMDB - Configuration Management Database

A lightweight, SQLite-based CMDB (Configuration Management Database) with a web interface for tracking servers, applications, services, and their dependencies.

## Features

- 🖥️ **Server Management** - Track physical and virtual servers
- 📱 **Application Inventory** - Manage applications and versions
- ⚙️ **Service Mapping** - Document services and their ports
- 🔗 **Dependency Tracking** - Map relationships between services
- 🔍 **Auto-Discovery** - Discover local system information
- 📊 **Dashboard** - Visual statistics and quick overview
- 📁 **Import/Export** - CSV import/export functionality
- 🚀 **No External Dependencies** - Uses SQLite (no database server needed!)

## Quick Start

### Option 1: Run with Python (Fastest)

```bash
# Clone the repository
git clone https://github.com/tysoncung/simple-cmdb.git
cd simple-cmdb

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py

# Open browser to http://localhost:5000
```

### Option 2: Run with Docker

```bash
# Clone the repository
git clone https://github.com/tysoncung/simple-cmdb.git
cd simple-cmdb

# Run with Docker Compose
docker-compose up -d

# Open browser to http://localhost:5000
```

### Option 3: Quick Docker Run

```bash
docker run -d -p 5000:5000 --name simple-cmdb \
  -v $(pwd)/data:/app/data \
  ghcr.io/tysoncung/simple-cmdb:latest
```

## Demo Mode - Try It Now!

### 1. Start the Application
```bash
python app.py
```

### 2. Discover Your Local System
- Click "Discover Local" button on the dashboard
- This will automatically populate your local machine's information

### 3. Add Sample Data
```bash
# Run the demo data script
python demo_data.py
```

### 4. Explore Features
- View servers, applications, and services
- Check the dependency map
- Export data as CSV
- Try the search functionality

## Usage Guide

### Adding Servers

1. **Manual Entry**
   - Click "Add Server" on the dashboard
   - Fill in hostname, IP, OS type, etc.
   - Click "Add Server"

2. **Auto-Discovery**
   - Click "Discover Local" to scan current system
   - Or use the discovery script for remote systems

3. **CSV Import**
   - Prepare CSV with columns: hostname, ip_address, os_type, os_version
   - Go to Import section
   - Upload CSV file

### Managing Applications

- Track application versions
- Set criticality levels (Low, Medium, High, Critical)
- Link applications to services

### Mapping Services

- Associate services with servers
- Document ports and protocols
- Track service status

### Tracking Dependencies

- Define service-to-service dependencies
- Visualize dependency chains
- Identify critical paths

## API Endpoints

The CMDB provides REST APIs for integration:

```bash
# Get statistics
curl http://localhost:5000/api/stats

# Discover local system
curl -X POST http://localhost:5000/api/discover/local

# Add server
curl -X POST http://localhost:5000/api/server/add \
  -H "Content-Type: application/json" \
  -d '{"hostname": "web01", "ip_address": "192.168.1.10"}'

# Export data
curl http://localhost:5000/api/export/servers > servers.csv
```

## Discovery Scripts

### Linux Discovery
```bash
# Discover remote Linux server
python discover_linux.py --host server.example.com --user admin
```

### Windows Discovery
```powershell
# Discover Windows machines
.\discover_windows.ps1 -ComputerName SERVER01
```

### Network Discovery
```bash
# Scan network range
python discover_network.py --range 192.168.1.0/24
```

## Database Schema

The CMDB uses SQLite with the following main tables:

- **servers** - Server inventory
- **applications** - Application catalog
- **services** - Service instances
- **dependencies** - Service relationships
- **discovery_history** - Discovery audit trail

## Configuration

Environment variables:
- `FLASK_ENV` - Set to 'production' for production use
- `DATABASE_PATH` - Custom database location (default: cmdb.db)
- `PORT` - Web server port (default: 5000)

## Screenshots

### Dashboard
- Statistics overview
- Recent servers
- Quick actions

### Servers View
- Complete server inventory
- Filtering and search
- Bulk operations

### Dependencies
- Visual dependency mapping
- Impact analysis
- Service relationships

## Development

### Project Structure
```
simple-cmdb/
├── app.py              # Main Flask application
├── templates/          # HTML templates
├── static/            # CSS, JS, images
├── discovery/         # Discovery scripts
├── requirements.txt   # Python dependencies
├── docker-compose.yml # Docker configuration
└── cmdb.db           # SQLite database
```

### Adding New Features
1. Extend the database schema in `app.py`
2. Add new routes and API endpoints
3. Create corresponding templates
4. Update the dashboard

## Backup and Restore

### Backup
```bash
# Backup database
cp cmdb.db cmdb_backup_$(date +%Y%m%d).db

# Export all data
python export_all.py
```

### Restore
```bash
# Restore database
cp cmdb_backup.db cmdb.db

# Import data
python import_data.py --file backup.json
```

## Troubleshooting

### Database Locked
```bash
# If database is locked, restart the application
pkill -f app.py
python app.py
```

### Port Already in Use
```bash
# Use a different port
PORT=8080 python app.py
```

### Discovery Not Working
```bash
# Check Python version (3.6+ required)
python --version

# Reinstall psutil
pip install --upgrade psutil
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file

## Support

- **Issues**: [GitHub Issues](https://github.com/tysoncung/simple-cmdb/issues)
- **Discussions**: [GitHub Discussions](https://github.com/tysoncung/simple-cmdb/discussions)

## Roadmap

- [ ] REST API authentication
- [ ] Bulk import/export
- [ ] Scheduled discovery
- [ ] Email notifications
- [ ] Dependency visualization graph
- [ ] Docker image scanning
- [ ] Cloud provider integration (AWS, Azure)
- [ ] Ansible integration
- [ ] Webhook support
- [ ] Multi-user support

## Credits

Built with:
- Flask - Web framework
- SQLite - Database
- Bootstrap - UI framework
- Chart.js - Charts
- psutil - System information

---

**Simple CMDB** - Making infrastructure management simple!