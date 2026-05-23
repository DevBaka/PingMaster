# PingMaster - Network Monitoring Tool

PingMaster ist ein leistungsstarkes, plattformübergreifendes **Network Monitoring Tool** und **Ping Scanner** für die automatische Netzwerküberwachung. Mit Host-Discovery, kontinuierlichem Ping-Monitoring, Response-Time-Tracking und einem Live-Dashboard ist PingMaster die ideale Lösung für Systemadministratoren und Netzwerk-Engineers zur Überwachung von Netzwerk-Verfügbarkeit und Performance.

![Screenshot](screenshot.png)

## Features

- **Automatische Netzwerk-Erkennung**: Erkennt automatisch lokale Netzwerke und alle aktiven Hosts mit **Network Discovery**
- **Kontinuierliches Monitoring**: Pingt alle Hosts kontinuierlich und überwacht deren Status in Echtzeit
- **Performance-Metriken**: Zeigt Response Times (RTT), Latenz und Packet Loss für jeden Host
- **Port-Scanning**: Scannt gängige Ports auf offene Verbindungen mit **Network Scanner**
- **Live-Dashboard**: Schönes Terminal-UI mit Rich Library für Echtzeit-Updates und **Network Visualization**
- **Konfigurierbar**: Alle Einstellungen können über `config.ini` angepasst werden
- **Logging**: Protokolliert alle Statusänderungen und Ereignisse für **Network Troubleshooting**
- **Multi-threading**: Parallele Überwachung für optimale Performance bei **Large Network Scanning**
- **Cross-Platform**: Läuft auf Windows, Linux und macOS als **Portable Network Tool**

## Installation

### Voraussetzungen

- Python 3.6 oder höher
- Administrator/Root-Rechte (für Netzwerk-Scanning)

### Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

Die benötigten Pakete sind:
- `python-nmap>=0.7.1` - Für Nmap-Integration und **Network Port Scanning**
- `psutil>=5.9.0` - Für Netzwerk-Interface-Erkennung und **System Monitoring** (ersetzt netifaces für bessere Kompatibilität)
- `rich>=13.7.0` - Für das Terminal-UI und **Console Dashboard**
- `python-dotenv>=1.0.0` - Für Umgebungsvariablen
- `setuptools>=65.5.0` - Für Paket-Management

### Optional: Als Python-Paket installieren

```bash
python setup.py install
```

## .exe erstellen (Windows Release)

Um PingMaster als ausführbare .exe-Datei für Windows zu erstellen, verwenden Sie PyInstaller:

### PyInstaller installieren

```bash
pip install pyinstaller
```

### .exe erstellen

**Einfache .exe (mit Konsole):**

```bash
pyinstaller --onefile network_monitor.py --name PingMaster
```

**.exe ohne Konsole (im Hintergrund):**

```bash
pyinstaller --onefile --noconsole network_monitor.py --name PingMaster
```

**.exe mit Icon und ohne Konsole:**

```bash
pyinstaller --onefile --noconsole --icon=icon.ico network_monitor.py --name PingMaster
```

**Erweiterte .exe mit allen Abhängigkeiten:**

```bash
pyinstaller --onefile --noconsole --add-data "config.ini;." --add-data "screenshot.png;." network_monitor.py --name PingMaster
```

### Build-Skript verwenden

Alternativ können Sie das bereitgestellte Build-Skript verwenden:

```bash
python build.py
```

Dies erstellt eine optimierte .exe im `dist/` Ordner.

### Release vorbereiten

Nach dem Build:

1. Die .exe aus `dist/` Ordner kopieren
2. `config.ini` und `screenshot.png` mit in das Release-Verzeichnis kopieren
3. Optional: Eine README.txt mit Installationsanweisungen hinzufügen
4. Alles in eine .zip-Datei packen

**Hinweis**: Die .exe enthält alle Python-Abhängigkeiten und kann ohne Python-Installation auf Windows ausgeführt werden.

## Verwendung

### Einfach starten

```bash
python network_monitor.py
```

PingMaster wird automatisch:
1. Alle lokalen Netzwerke erkennen mit **Network Discovery**
2. Alle aktiven Hosts im Netzwerk scannen mit **Host Discovery**
3. Mit dem **Ping Monitoring** beginnen
4. Ein Live-Dashboard für **Network Visualization** anzeigen

### Mit sudo (Linux/macOS)

Auf Linux und macOS sind Root-Rechte für Netzwerk-Scanning erforderlich:

```bash
sudo python network_monitor.py
```

### Als Administrator (Windows)

Auf Windows als Administrator ausführen.

## Konfiguration

Die Einstellungen können in der `config.ini` Datei angepasst werden:

```ini
[network]
network = auto              # 'auto' für automatische Erkennung oder z.B. '192.168.1.0/24'
scan_interval = 300         # Netzwerk-Scan-Intervall in Sekunden (5 Minuten)
timeout = 2                 # Ping-Timeout in Sekunden

[logging]
level = INFO               # Log-Level: DEBUG, INFO, WARNING, ERROR
file = pingmaster.log      # Log-Datei-Pfad

[monitoring]
ping_count = 1             # Anzahl der Pings pro Check
update_interval = 5        # UI-Update-Intervall in Sekunden
max_history = 10           # Anzahl der Response-Time-Werte die gespeichert werden

[ports]
common_ports = 21,22,23,80,443,3389,5900  # Zu scannende Ports
```

## Dashboard

Das PingMaster Live-Dashboard zeigt folgende Informationen für jeden Host in Echtzeit:

![Screenshot](screenshot.png)

- **IP**: IP-Adresse des Hosts
- **Hostname**: Aufgelöster Hostname (falls verfügbar) für **Host Identification**
- **Status**: UP (grün) oder DOWN (rot) für **Network Availability Monitoring**
- **Last Seen**: Zeit des letzten erfolgreichen Pings
- **Avg. RTT**: Durchschnittliche Response-Time in Millisekunden für **Latency Monitoring**
- **Packet Loss %**: Prozentsatz verlorener Pakete für **Network Quality Assessment**

### Steuerung

- `Ctrl+C`: Beendet das Monitoring

## Architektur

### Hauptkomponenten

- **network_monitor.py**: Hauptanwendung mit Monitoring-Logik und UI für **Network Monitoring**
- **nettool.py**: Legacy-Tool mit erweiterten Netzwerk-Funktionen für **Network Scanning**
- **config_manager.py**: Konfigurationsverwaltung
- **logger.py**: Logging-System mit Host-spezifischen Loggern für **Network Logging**

### Datenstrukturen

- **HostStatus**: Trackt Status, Response-Times, Packet-Loss und offene Ports für jeden Host
- **NetworkMonitor**: Hauptklasse für Netzwerk-Discovery und Monitoring

## Legacy-Tool (nettool.py)

PingMaster enthält auch ein älteres Tool `nettool.py` mit zusätzlichen Funktionen für **Advanced Network Scanning**:

### Verfügbare Optionen

```bash
python nettool.py --domain <domain>      # Ping eine Domain
python nettool.py -d <domain>            # Ping eine Domain (kurz)
python nettool.py --ip <ip>              # Scan ein IP-Range
python nettool.py --subnet <subnet>      # Setze Subnet
python nettool.py -p                     # Starte Ping-Monitoring
python nettool.py --localIP              # Zeige lokale IPs
python nettool.py -lip                   # Zeige lokale IPs (kurz)
python nettool.py -a                     # Auto-Scan
python nettool.py --sip <x.x.x.x/xx>     # Subnet mit CIDR
python nettool.py --hostname             # Zeige Hostnames (langsamer)
```

### Beispiel

```bash
# Auto-Scan des lokalen Netzwerks mit Ping-Monitoring
python nettool.py -a -p

# Bestimmtes Subnet scannen
python nettool.py --sip 192.168.1.0/24 -p
```

## Troubleshooting

### Keine Hosts gefunden

- Stellen Sie sicher, dass Sie mit dem Netzwerk verbunden sind
- Überprüfen Sie die Firewall-Einstellungen für **Network Discovery**
- Führen Sie das Tool als Administrator/Root aus für **Network Scanning**

### Ping schlägt fehl

- Einige Firewalls blockieren ICMP-Pakete
- Überprüfen Sie die Timeout-Einstellung in `config.ini` für **Ping Timeout Configuration**

### Hostname-Auflösung funktioniert nicht

- Dies ist normal, wenn DNS nicht korrekt konfiguriert ist
- Die IP-Adresse wird stattdessen für **Host Identification** angezeigt

## Lizenz

MIT License

## Beiträge

Beiträge sind willkommen! Fühlen Sie sich frei, Issues zu öffnen oder Pull Requests zu erstellen.

## Autor

Erstellt vor 7 Jahren als persönliches Netzwerk-Monitoring-Tool. PingMaster ist ein Open-Source **Network Monitoring Tool** für Systemadministratoren und Netzwerk-Engineers.

---

**Keywords**: Network Monitoring, Ping Tool, Network Scanner, Host Discovery, Network Visualization, Latency Monitoring, Packet Loss, Network Troubleshooting, Python Network Tool, Cross-Platform Network Monitor

