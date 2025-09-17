#!/usr/bin/env python3
"""
Demo data generator for Simple CMDB
Populates the database with sample data for demonstration
"""

import sqlite3
import random
from datetime import datetime, timedelta

def create_demo_data():
    """Create demo data in the CMDB database"""
    conn = sqlite3.connect('cmdb.db')
    cursor = conn.cursor()

    print("Adding demo servers...")
    servers = [
        ('web-prod-01', '10.0.1.10', 'Linux', 'Ubuntu 22.04', 'production', 'active', 'DevOps Team', 'Primary web server'),
        ('web-prod-02', '10.0.1.11', 'Linux', 'Ubuntu 22.04', 'production', 'active', 'DevOps Team', 'Secondary web server'),
        ('db-prod-01', '10.0.2.10', 'Linux', 'CentOS 8', 'production', 'active', 'Database Team', 'Primary database server'),
        ('db-prod-02', '10.0.2.11', 'Linux', 'CentOS 8', 'production', 'active', 'Database Team', 'Replica database server'),
        ('cache-prod-01', '10.0.3.10', 'Linux', 'Ubuntu 20.04', 'production', 'active', 'DevOps Team', 'Redis cache server'),
        ('app-staging-01', '10.1.1.10', 'Linux', 'Ubuntu 22.04', 'staging', 'active', 'Dev Team', 'Staging application server'),
        ('db-staging-01', '10.1.2.10', 'Linux', 'CentOS 8', 'staging', 'active', 'Dev Team', 'Staging database'),
        ('monitor-01', '10.0.4.10', 'Linux', 'Ubuntu 22.04', 'production', 'active', 'SRE Team', 'Monitoring server'),
        ('backup-01', '10.0.5.10', 'Linux', 'Rocky Linux 9', 'production', 'active', 'Ops Team', 'Backup server'),
        ('dev-workstation-01', '192.168.1.100', 'Windows', 'Windows 11', 'development', 'active', 'John Doe', 'Development workstation'),
        ('dev-workstation-02', '192.168.1.101', 'macOS', 'Ventura', 'development', 'active', 'Jane Smith', 'Development workstation'),
        ('ci-cd-01', '10.0.6.10', 'Linux', 'Ubuntu 22.04', 'production', 'active', 'DevOps Team', 'Jenkins CI/CD server'),
    ]

    for server in servers:
        cursor.execute('''
            INSERT OR IGNORE INTO servers (hostname, ip_address, os_type, os_version, environment, status, owner, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', server)

    print("Adding demo applications...")
    applications = [
        ('E-Commerce Platform', '3.2.1', 'web', 'Java', 'critical', 'active', 'Product Team', 'Main e-commerce application'),
        ('Customer API', '2.1.0', 'api', 'Python', 'critical', 'active', 'API Team', 'Customer data API'),
        ('Payment Gateway', '1.5.3', 'api', 'Go', 'critical', 'active', 'Payment Team', 'Payment processing service'),
        ('MySQL Database', '8.0.32', 'database', 'SQL', 'critical', 'active', 'Database Team', 'Primary database'),
        ('Redis Cache', '7.0.5', 'cache', 'C', 'high', 'active', 'DevOps Team', 'In-memory cache'),
        ('Elasticsearch', '8.7.0', 'database', 'Java', 'high', 'active', 'Search Team', 'Search engine'),
        ('RabbitMQ', '3.11.13', 'queue', 'Erlang', 'high', 'active', 'Messaging Team', 'Message broker'),
        ('Prometheus', '2.42.0', 'monitoring', 'Go', 'medium', 'active', 'SRE Team', 'Metrics monitoring'),
        ('Grafana', '9.4.7', 'monitoring', 'Go', 'medium', 'active', 'SRE Team', 'Metrics visualization'),
        ('Jenkins', '2.387.1', 'ci/cd', 'Java', 'medium', 'active', 'DevOps Team', 'CI/CD automation'),
        ('Nginx', '1.22.1', 'web', 'C', 'high', 'active', 'DevOps Team', 'Web server/Load balancer'),
        ('Backup Manager', '2.0.1', 'utility', 'Python', 'high', 'active', 'Ops Team', 'Backup automation'),
    ]

    for app in applications:
        cursor.execute('''
            INSERT OR IGNORE INTO applications (name, version, type, language, criticality, status, owner, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', app)

    print("Adding demo services...")
    # Get server and application IDs
    cursor.execute('SELECT id, hostname FROM servers')
    server_map = {hostname: id for id, hostname in cursor.fetchall()}

    cursor.execute('SELECT id, name FROM applications')
    app_map = {name: id for id, name in cursor.fetchall()}

    services = [
        ('nginx-web', server_map.get('web-prod-01'), app_map.get('Nginx'), 80, 'http', 'running'),
        ('nginx-ssl', server_map.get('web-prod-01'), app_map.get('Nginx'), 443, 'https', 'running'),
        ('ecommerce-app', server_map.get('web-prod-01'), app_map.get('E-Commerce Platform'), 8080, 'http', 'running'),
        ('customer-api', server_map.get('web-prod-02'), app_map.get('Customer API'), 5000, 'http', 'running'),
        ('payment-service', server_map.get('web-prod-02'), app_map.get('Payment Gateway'), 8443, 'https', 'running'),
        ('mysql-primary', server_map.get('db-prod-01'), app_map.get('MySQL Database'), 3306, 'tcp', 'running'),
        ('mysql-replica', server_map.get('db-prod-02'), app_map.get('MySQL Database'), 3306, 'tcp', 'running'),
        ('redis-cache', server_map.get('cache-prod-01'), app_map.get('Redis Cache'), 6379, 'tcp', 'running'),
        ('elasticsearch', server_map.get('monitor-01'), app_map.get('Elasticsearch'), 9200, 'http', 'running'),
        ('prometheus', server_map.get('monitor-01'), app_map.get('Prometheus'), 9090, 'http', 'running'),
        ('grafana', server_map.get('monitor-01'), app_map.get('Grafana'), 3000, 'http', 'running'),
        ('rabbitmq', server_map.get('app-staging-01'), app_map.get('RabbitMQ'), 5672, 'tcp', 'running'),
        ('jenkins', server_map.get('ci-cd-01'), app_map.get('Jenkins'), 8080, 'http', 'running'),
        ('backup-service', server_map.get('backup-01'), app_map.get('Backup Manager'), 9001, 'tcp', 'running'),
    ]

    service_ids = {}
    for service in services:
        cursor.execute('''
            INSERT OR IGNORE INTO services (name, server_id, application_id, port, protocol, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', service)
        service_ids[service[0]] = cursor.lastrowid

    print("Adding demo dependencies...")
    # Get service IDs
    cursor.execute('SELECT id, name FROM services')
    service_map = {name: id for id, name in cursor.fetchall()}

    dependencies = [
        (service_map.get('ecommerce-app'), service_map.get('customer-api'), 'E-commerce app calls customer API'),
        (service_map.get('ecommerce-app'), service_map.get('payment-service'), 'E-commerce app uses payment service'),
        (service_map.get('ecommerce-app'), service_map.get('mysql-primary'), 'E-commerce app connects to database'),
        (service_map.get('ecommerce-app'), service_map.get('redis-cache'), 'E-commerce app uses Redis for caching'),
        (service_map.get('customer-api'), service_map.get('mysql-primary'), 'Customer API reads from database'),
        (service_map.get('payment-service'), service_map.get('mysql-primary'), 'Payment service stores transactions'),
        (service_map.get('payment-service'), service_map.get('rabbitmq'), 'Payment service sends messages to queue'),
        (service_map.get('nginx-web'), service_map.get('ecommerce-app'), 'Nginx proxies to e-commerce app'),
        (service_map.get('nginx-ssl'), service_map.get('ecommerce-app'), 'Nginx SSL proxies to e-commerce app'),
        (service_map.get('mysql-replica'), service_map.get('mysql-primary'), 'Database replication'),
        (service_map.get('prometheus'), service_map.get('ecommerce-app'), 'Prometheus scrapes metrics'),
        (service_map.get('prometheus'), service_map.get('customer-api'), 'Prometheus scrapes metrics'),
        (service_map.get('grafana'), service_map.get('prometheus'), 'Grafana queries Prometheus'),
        (service_map.get('backup-service'), service_map.get('mysql-primary'), 'Backup service backs up database'),
        (service_map.get('elasticsearch'), service_map.get('ecommerce-app'), 'Elasticsearch indexes app logs'),
    ]

    for dep in dependencies:
        if dep[0] and dep[1]:  # Only insert if both IDs exist
            cursor.execute('''
                INSERT OR IGNORE INTO dependencies (source_service_id, target_service_id, description)
                VALUES (?, ?, ?)
            ''', dep)

    conn.commit()
    conn.close()

    print("\n✅ Demo data added successfully!")
    print("\nSummary:")
    print(f"  - {len(servers)} servers")
    print(f"  - {len(applications)} applications")
    print(f"  - {len(services)} services")
    print(f"  - {len([d for d in dependencies if d[0] and d[1]])} dependencies")
    print("\nYou can now start the application with: python app.py")

if __name__ == '__main__':
    create_demo_data()