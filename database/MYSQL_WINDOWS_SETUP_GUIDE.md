# Windows MySQL Setup & Integration Guide

This guide provides instructions for setting up **MySQL on Windows 10/11** for the **VIT Vellore Intelligent FAQ Chatbot**.

> [!NOTE]
> The chatbot works **100% out-of-the-box** without MySQL, using the bundled verified JSON/CSV knowledge base and embedded SQLite for session/chat logging. MySQL is an optional advanced integration.

---

## Option A: Using MySQL Community Installer (Recommended for Beginners)

1. Download the **MySQL Community Server (MSI Installer)** from:
   [https://dev.mysql.com/downloads/installer/](https://dev.mysql.com/downloads/installer/)
2. Run `mysql-installer-community-*.msi`.
3. Choose **Server only** or **Developer Default**.
4. During configuration:
   - Port: `3306` (default)
   - Authentication: Use Strong Password Encryption
   - Set a root password (e.g., `vit@123` or your own password)
5. Complete installation and ensure the Windows service `MySQL80` is running.

---

## Option B: Using MySQL ZIP Archive (Manual CLI Installation)

If you downloaded a ZIP archive (e.g., `mysql-8.x.x-winx64.zip`) without an installer:

### 1. Extract the ZIP
Extract to a permanent directory, for example: `C:\mysql`

### 2. Create `my.ini` Configuration File
Inside `C:\mysql`, create a file named `my.ini` with:

```ini
[mysqld]
basedir=C:/mysql
datadir=C:/mysql/data
port=3306
character-set-server=utf8mb4
default-authentication-plugin=mysql_native_password
```

### 3. Initialize the Data Directory (PowerShell as Administrator)
Open PowerShell as **Administrator** and run:

```powershell
cd C:\mysql\bin
.\mysqld.exe --initialize-insecure --console
```
*(Note: `--initialize-insecure` creates the root user with an empty password so you can set it next.)*

### 4. Install and Start the Windows Service
```powershell
.\mysqld.exe --install MySQL
Start-Service MySQL
```

### 5. Secure Root Password
Log into the MySQL shell:
```powershell
.\mysql.exe -u root
```
In the MySQL prompt, set your password:
```sql
ALTER USER 'root'@'localhost' IDENTIFIED BY 'vitpassword123';
FLUSH PRIVILEGES;
EXIT;
```

---

## Integrating MySQL with the VIT Vellore Chatbot

### 1. Install Python MySQL Driver
In your project virtual environment or terminal:
```powershell
pip install pymysql cryptography
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` in the project root:
```powershell
Copy-Item .env.example .env
```

Open `.env` and set:
```env
USE_MYSQL=true
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_actual_password
MYSQL_DATABASE=vit_faq_db
```

### 3. Run Automated Database Migration & Import
Execute the automated importer script from the project root:
```powershell
python database/import_to_mysql.py
```

Expected output:
```text
======================================================================
Importing VIT Vellore FAQs to MySQL Database
======================================================================
Target MySQL Host: localhost:3306
Database:          vit_faq_db

Populating 195 FAQs into MySQL...
[Success] Successfully imported 195 records into MySQL!
```

---

## Troubleshooting Common Windows Issues

| Error | Cause | Resolution |
| :--- | :--- | :--- |
| `Can't connect to MySQL server on 'localhost:3306'` | Service is stopped | Run `Start-Service MySQL` in Admin PowerShell. |
| `Access denied for user 'root'@'localhost'` | Wrong password | Update `MYSQL_PASSWORD` in `.env` to match your root password. |
| `ModuleNotFoundError: No module named 'pymysql'` | Missing package | Run `pip install pymysql`. |
| Port 3306 already in use | Conflicting service (e.g. XAMPP/MariaDB) | Change port in `my.ini` and `.env` to `3307`. |
