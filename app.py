#!/usr/bin/env python3
"""
Simple CMDB - A lightweight Configuration Management Database
Using SQLite for storage and Flask for web interface
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
import sqlite3
import json
from datetime import datetime
import os
import psutil
import socket
import subprocess
import platform
from typing import Dict, List, Optional
import csv
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cmdb-secret-key-change-in-production'

# Database setup
DB_PATH = 'cmdb.db'

def init_db():
    """Initialize the CMDB database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Servers table
    c.execute('''
        CREATE TABLE IF NOT EXISTS servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hostname TEXT UNIQUE NOT NULL,
            ip_address TEXT,
            os_type TEXT,
            os_version TEXT,
            cpu_cores INTEGER,
            memory_gb REAL,
            disk_gb REAL,
            environment TEXT,
            status TEXT DEFAULT 'active',
            location TEXT,
            owner TEXT,
            notes TEXT,
            last_seen TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Applications table
    c.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            version TEXT,
            type TEXT,
            language TEXT,
            repository_url TEXT,
            documentation_url TEXT,
            owner TEXT,
            criticality TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Services table
    c.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER,
            application_id INTEGER,
            service_name TEXT NOT NULL,
            port INTEGER,
            protocol TEXT,
            status TEXT DEFAULT 'running',
            process_name TEXT,
            start_command TEXT,
            config_file TEXT,
            log_file TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (server_id) REFERENCES servers (id) ON DELETE CASCADE,
            FOREIGN KEY (application_id) REFERENCES applications (id) ON DELETE SET NULL
        )
    ''')

    # Dependencies table
    c.execute('''
        CREATE TABLE IF NOT EXISTS dependencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_service_id INTEGER,
            target_service_id INTEGER,
            dependency_type TEXT,
            port INTEGER,
            protocol TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_service_id) REFERENCES services (id) ON DELETE CASCADE,
            FOREIGN KEY (target_service_id) REFERENCES services (id) ON DELETE CASCADE
        )
    ''')

    # Discovery history table
    c.execute('''
        CREATE TABLE IF NOT EXISTS discovery_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER,
            discovery_type TEXT,
            data TEXT,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (server_id) REFERENCES servers (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()

# Routes
@app.route('/')
def index():
    """Main dashboard"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get statistics
    stats = {
        'servers': c.execute('SELECT COUNT(*) FROM servers').fetchone()[0],
        'applications': c.execute('SELECT COUNT(*) FROM applications').fetchone()[0],
        'services': c.execute('SELECT COUNT(*) FROM services').fetchone()[0],
        'dependencies': c.execute('SELECT COUNT(*) FROM dependencies').fetchone()[0]
    }

    # Get recent servers
    recent_servers = c.execute('''
        SELECT * FROM servers
        ORDER BY created_at DESC
        LIMIT 5
    ''').fetchall()

    conn.close()

    return render_template('dashboard.html', stats=stats, recent_servers=recent_servers)

@app.route('/servers')
def servers():
    """List all servers"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    servers = c.execute('SELECT * FROM servers ORDER BY hostname').fetchall()
    conn.close()

    return render_template('servers.html', servers=servers)

@app.route('/server/<int:server_id>')
def server_detail(server_id):
    """Server details page"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    server = c.execute('SELECT * FROM servers WHERE id = ?', (server_id,)).fetchone()

    services = c.execute('''
        SELECT s.*, a.name as app_name
        FROM services s
        LEFT JOIN applications a ON s.application_id = a.id
        WHERE s.server_id = ?
    ''', (server_id,)).fetchall()

    conn.close()

    return render_template('server_detail.html', server=server, services=services)

@app.route('/applications')
def applications():
    """List all applications"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    apps = c.execute('SELECT * FROM applications ORDER BY name').fetchall()
    conn.close()

    return render_template('applications.html', applications=apps)

@app.route('/services')
def services():
    """List all services with their relationships"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    services_list = c.execute('''
        SELECT s.*, srv.hostname, a.name as app_name
        FROM services s
        LEFT JOIN servers srv ON s.server_id = srv.id
        LEFT JOIN applications a ON s.application_id = a.id
        ORDER BY s.service_name
    ''').fetchall()

    conn.close()

    return render_template('services.html', services=services_list)

@app.route('/dependencies')
def dependencies():
    """Show service dependencies"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    deps = c.execute('''
        SELECT d.*,
               s1.service_name as source_service,
               s2.service_name as target_service,
               srv1.hostname as source_server,
               srv2.hostname as target_server
        FROM dependencies d
        JOIN services s1 ON d.source_service_id = s1.id
        JOIN services s2 ON d.target_service_id = s2.id
        JOIN servers srv1 ON s1.server_id = srv1.id
        JOIN servers srv2 ON s2.server_id = srv2.id
    ''').fetchall()

    conn.close()

    return render_template('dependencies.html', dependencies=deps)

@app.route('/discover')
def discover():
    """Discovery page"""
    return render_template('discover.html')

@app.route('/api/discover/local', methods=['POST'])
def discover_local():
    """Discover local system information"""
    try:
        # Get system information
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)

        system_info = {
            'hostname': hostname,
            'ip_address': ip_address,
            'os_type': platform.system(),
            'os_version': platform.version(),
            'cpu_cores': psutil.cpu_count(),
            'memory_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'disk_gb': round(psutil.disk_usage('/').total / (1024**3), 2),
            'platform': platform.platform(),
            'architecture': platform.machine(),
            'processor': platform.processor()
        }

        # Get running services (processes)
        services = []
        for proc in psutil.process_iter(['pid', 'name', 'status', 'memory_percent']):
            try:
                pinfo = proc.info
                if pinfo['memory_percent'] > 0.1:  # Only significant processes
                    services.append({
                        'name': pinfo['name'],
                        'pid': pinfo['pid'],
                        'status': pinfo['status'],
                        'memory_percent': round(pinfo['memory_percent'], 2)
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Get network connections
        connections = []
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'LISTEN':
                connections.append({
                    'port': conn.laddr.port,
                    'address': conn.laddr.ip,
                    'type': 'tcp' if conn.type == 1 else 'udp'
                })

        # Store in database
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Insert or update server
        c.execute('''
            INSERT OR REPLACE INTO servers
            (hostname, ip_address, os_type, os_version, cpu_cores, memory_gb, disk_gb, last_seen, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
        ''', (
            hostname, ip_address, system_info['os_type'],
            system_info['os_version'][:50] if system_info['os_version'] else 'Unknown',
            system_info['cpu_cores'], system_info['memory_gb'],
            system_info['disk_gb'], datetime.now()
        ))

        server_id = c.lastrowid if c.lastrowid else c.execute(
            'SELECT id FROM servers WHERE hostname = ?', (hostname,)
        ).fetchone()[0]

        # Store discovery data
        c.execute('''
            INSERT INTO discovery_history (server_id, discovery_type, data)
            VALUES (?, 'local_discovery', ?)
        ''', (server_id, json.dumps({
            'system': system_info,
            'services': services[:20],  # Top 20 services
            'connections': connections
        })))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'system': system_info,
                'services_count': len(services),
                'connections_count': len(connections)
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/server/add', methods=['POST'])
def add_server():
    """Add a new server"""
    data = request.json

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        c.execute('''
            INSERT INTO servers
            (hostname, ip_address, os_type, os_version, environment, owner, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['hostname'], data.get('ip_address'), data.get('os_type'),
            data.get('os_version'), data.get('environment', 'production'),
            data.get('owner'), data.get('notes'), 'active'
        ))

        conn.commit()
        server_id = c.lastrowid

        return jsonify({'success': True, 'server_id': server_id})

    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'Server already exists'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/application/add', methods=['POST'])
def add_application():
    """Add a new application"""
    data = request.json

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        c.execute('''
            INSERT INTO applications
            (name, version, type, language, owner, criticality, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['name'], data.get('version'), data.get('type'),
            data.get('language'), data.get('owner'),
            data.get('criticality', 'medium'), data.get('notes')
        ))

        conn.commit()
        app_id = c.lastrowid

        return jsonify({'success': True, 'application_id': app_id})

    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'Application already exists'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/service/add', methods=['POST'])
def add_service():
    """Add a new service"""
    data = request.json

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        c.execute('''
            INSERT INTO services
            (server_id, application_id, service_name, port, protocol, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['server_id'], data.get('application_id'),
            data['service_name'], data.get('port'),
            data.get('protocol', 'tcp'), data.get('status', 'running')
        ))

        conn.commit()
        service_id = c.lastrowid

        return jsonify({'success': True, 'service_id': service_id})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/dependency/add', methods=['POST'])
def add_dependency():
    """Add a service dependency"""
    data = request.json

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        c.execute('''
            INSERT INTO dependencies
            (source_service_id, target_service_id, dependency_type, description)
            VALUES (?, ?, ?, ?)
        ''', (
            data['source_service_id'], data['target_service_id'],
            data.get('dependency_type', 'requires'), data.get('description')
        ))

        conn.commit()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/stats')
def api_stats():
    """Get CMDB statistics"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    stats = {
        'servers': {
            'total': c.execute('SELECT COUNT(*) FROM servers').fetchone()[0],
            'active': c.execute("SELECT COUNT(*) FROM servers WHERE status='active'").fetchone()[0],
            'by_os': dict(c.execute('SELECT os_type, COUNT(*) FROM servers GROUP BY os_type').fetchall()),
            'by_env': dict(c.execute('SELECT environment, COUNT(*) FROM servers WHERE environment IS NOT NULL GROUP BY environment').fetchall())
        },
        'applications': {
            'total': c.execute('SELECT COUNT(*) FROM applications').fetchone()[0],
            'by_criticality': dict(c.execute('SELECT criticality, COUNT(*) FROM applications WHERE criticality IS NOT NULL GROUP BY criticality').fetchall())
        },
        'services': {
            'total': c.execute('SELECT COUNT(*) FROM services').fetchone()[0],
            'running': c.execute("SELECT COUNT(*) FROM services WHERE status='running'").fetchone()[0]
        },
        'dependencies': {
            'total': c.execute('SELECT COUNT(*) FROM dependencies').fetchone()[0]
        }
    }

    conn.close()

    return jsonify(stats)

@app.route('/api/export/<table>')
def export_table(table):
    """Export table data as CSV"""
    if table not in ['servers', 'applications', 'services', 'dependencies']:
        return jsonify({'error': 'Invalid table'}), 400

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    rows = c.execute(f'SELECT * FROM {table}').fetchall()

    # Create CSV
    output = io.StringIO()
    if rows:
        writer = csv.writer(output)
        writer.writerow(rows[0].keys())  # Headers
        writer.writerows([list(row) for row in rows])

    conn.close()

    # Create response
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'{table}_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

@app.route('/api/import/<table>', methods=['POST'])
def import_table(table):
    """Import CSV data"""
    if table not in ['servers', 'applications']:
        return jsonify({'error': 'Invalid table'}), 400

    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file provided'}), 400

    # Read CSV
    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    csv_reader = csv.DictReader(stream)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    imported = 0
    errors = []

    for row in csv_reader:
        try:
            if table == 'servers':
                c.execute('''
                    INSERT OR IGNORE INTO servers
                    (hostname, ip_address, os_type, os_version, environment, owner)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('hostname'), row.get('ip_address'),
                    row.get('os_type'), row.get('os_version'),
                    row.get('environment'), row.get('owner')
                ))
            elif table == 'applications':
                c.execute('''
                    INSERT OR IGNORE INTO applications
                    (name, version, type, language, owner)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    row.get('name'), row.get('version'),
                    row.get('type'), row.get('language'), row.get('owner')
                ))

            if c.rowcount > 0:
                imported += 1

        except Exception as e:
            errors.append(f"Row error: {str(e)}")

    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'imported': imported,
        'errors': errors
    })

if __name__ == '__main__':
    init_db()

    port = int(os.environ.get('PORT', 5000))
    # Check if running in Docker
    if os.environ.get('DOCKER_CONTAINER'):
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        app.run(host='0.0.0.0', port=port, debug=True)