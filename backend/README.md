# Forensic Image Storage System - Backend

A secure forensic image storage system designed for crime-scene photos with encryption, integrity verification, and authentication.

## Features

- **Secure User Authentication**: SHA-256 password hashing with unique salt per user
- **AES-256-CBC Encryption**: Image encryption using AES-256 cipher in CBC mode
- **HMAC Verification**: Integrity checking using HMAC-SHA256
- **PostgreSQL Database**: Persistent storage for users, cases, and image metadata
- **HTTPS Support**: Secure communication over TLS/SSL

## Technology Stack

- **Java 17**
- **Spring Boot 3.2.0**
- **PostgreSQL**
- **Maven**
- **JWT for authentication**

## Project Structure

```
backend/
├── src/main/java/com/forensic/
│   ├── ForensicImageStorageApplication.java
│   ├── controller/
│   │   ├── UserController.java
│   │   ├── ImageController.java
│   │   └── CaseController.java
│   ├── dto/
│   │   ├── AuthRequest.java
│   │   ├── AuthResponse.java
│   │   ├── ImageUploadResponse.java
│   │   └── ImageVerifyResponse.java
│   ├── entity/
│   │   ├── User.java
│   │   ├── Case.java
│   │   └── Image.java
│   ├── repository/
│   │   ├── UserRepository.java
│   │   ├── CaseRepository.java
│   │   └── ImageRepository.java
│   └── service/
│       ├── PasswordService.java      
│       ├── CryptoService.java        
│       ├── HmacService.java           
│       └── KeyManagementService.java  
├── src/main/resources/
│   ├── application.properties
│   └── keystore.p12                  
├── config/
│   ├── keys.bin                       # 🔒 AES-256 key 
│   └── hmac.bin                       # 🔒 HMAC key
├── .gitignore                       
└── pom.xml
```

## Setup Instructions

### Prerequisites

1. Java 17 or higher
2. Maven 3.6+
3. PostgreSQL 12+

### Database Setup

1. Install PostgreSQL and create a database:

```sql
CREATE DATABASE forensic_db;
CREATE USER forensic_user WITH PASSWORD 'forensic_password';
GRANT ALL PRIVILEGES ON DATABASE forensic_db TO forensic_user;
```

2. The application will automatically create tables on startup using Hibernate DDL.

### SSL Certificate Generation (for HTTPS)

Generate a self-signed certificate for development (use alias `forensic-ssl`):

```bash
keytool -genkeypair -alias forensic-ssl -keyalg RSA -keysize 2048 \
  -storetype PKCS12 -keystore src/main/resources/keystore.p12 \
  -validity 365 -storepass forensic123 -keypass forensic123 \
  -dname "CN=localhost, OU=Forensics, O=InfoSec, L=City, ST=State, C=US"
```

**Windows (if keytool not in PATH):**
```bash
"C:\Program Files\Java\jdk-23\bin\keytool.exe" -genkeypair -alias forensic-ssl -keyalg RSA -keysize 2048 -storetype PKCS12 -keystore src\main\resources\keystore.p12 -validity 365 -storepass forensic123 -keypass forensic123 -dname "CN=localhost, OU=Forensics, O=InfoSec, L=City, ST=State, C=US"
```

### Build and Run

1. Clone the repository
2. Navigate to the backend directory
3. Update `application.properties` with your database credentials
4. Build the project:

```bash
mvn clean install
```

5. Run the application:

```bash
mvn spring-boot:run
```

The server will start on `https://localhost:8443`

## API Endpoints

### User Authentication

#### Signup
```
POST /api/user/signup
Content-Type: application/json

{
  "username": "forensic_user",
  "password": "secure_password"
}
```

#### Login
```
POST /api/user/login
Content-Type: application/json

{
  "username": "forensic_user",
  "password": "secure_password"
}
```

### Case Management

#### Create Case
```
POST /api/case/create
Content-Type: application/json

{
  "caseName": "Case #2024-001",
  "description": "Crime scene investigation"
}
```

### Image Operations

#### Upload Image
```
POST /api/image/upload
Content-Type: multipart/form-data

file: [image file]
caseId: [case ID]
description: [optional description]
```

#### View Image
```
GET /api/image/view/{id}
```

Verifies HMAC and returns decrypted image if valid.

#### Verify Image Integrity
```
GET /api/image/verify/{id}
```

Returns JSON with integrity status:
```json
{
  "imageId": 1,
  "filename": "evidence.jpg",
  "isValid": true,
  "message": "Image integrity verified successfully."
}
```

#### List Images by Case
```
GET /api/image/list/{caseId}
```

## Security Features

### 🔐 Secure Password Authentication
- **Algorithm**: SHA-256 hashing
- **Salt**: Unique 16-byte random salt per user
- **Storage**: Password hash (Base64) and salt stored separately in database
- **Verification**: Constant-time comparison to prevent timing attacks
- **Security Benefits**:
  - Unique salt prevents rainbow table attacks
  - One-way hash function (cannot reverse)
  - Salt stored in database for verification

### Image Encryption
- Algorithm: AES-256 (Advanced Encryption Standard)
- Mode: CBC (Cipher Block Chaining)
- IV: 16-byte random IV per image, prepended to ciphertext
- **Key Management** 🔐:
  - Keys stored in `.bin` files
  - PBKDF2 derivation with 65,536 iterations
  - Environment-based configuration via `.env` files
  - Never stored in plaintext or version control

### Integrity Verification
- Algorithm: HMAC-SHA256
- Computed over: Entire encrypted file (IV + ciphertext)
- Storage: Base64 encoded in database

### Authentication
- SHA-256 password hashing with unique salt per user
- Secure password verification with constant-time comparison
- User registration and login endpoints
- Note: JWT tokens and session management can be added for enhanced security

## Configuration

### 1. Application Properties

Edit `src/main/resources/application.properties`:

```properties
# Server
server.port=8443
server.ssl.key-alias=forensic-ssl

# Database
spring.datasource.url=jdbc:postgresql://localhost:5432/forensic_db
spring.datasource.username=forensic_user
spring.datasource.password=forensic_password

# Upload Directory (use absolute path on Windows)
app.upload.dir=C:/Users/YOUR_USERNAME/Desktop/InfoSec/uploads/encrypted-images

# Secure Key Management 🔐
app.crypto.use.sam.file=true
sam.file.aes.path=./config/keys.bin
sam.file.hmac.path=./config/hmac.bin

# Legacy: Fallback to hardcoded key (NOT recommended, testing only)
app.crypto.aes.key=ForensicImageStorageKey123456789
app.crypto.hmac.key=forensicHmacSecretKey2024
```

### 2. Key Files Setup 🔒

Your system uses **pre-configured constant keys** stored in `.bin` files:
- `config/keys.bin` - AES-256 encryption key (32 bytes)
- `config/hmac.bin` - HMAC-SHA256 key (32 bytes)

These files are already configured with your constant keys and ready to use.

⚠️ **Important**:
- SSL alias must be `forensic-ssl`
- Use absolute path for uploads on Windows
- Never commit `*.bin` files (already in `.gitignore`)
- Back up your `.bin` files securely - losing them means you can't decrypt data!

## Testing with cURL

### Signup
```bash
curl -k -X POST https://localhost:8443/api/user/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'
```

### Login
```bash
curl -k -X POST https://localhost:8443/api/user/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'
```

### Upload Image
```bash
curl -k -X POST https://localhost:8443/api/image/upload \
  -F "file=@/path/to/image.jpg" \
  -F "caseId=1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Important Notes

### ⚠️ SECURITY WARNINGS

1. **Password Security**: Passwords are hashed with SHA-256 and unique salt. For production, consider using bcrypt or Argon2 for additional security.
2. **Change default keys in production!** The AES-256 key and HMAC key should be stored securely (environment variables, key vault).
3. The self-signed certificate is for development only. Use a proper CA-signed certificate in production.
4. Image files are stored in the filesystem. Ensure proper file permissions and backup strategies.
5. The upload directory must be writable by the application.
6. **Database Migration**: Existing users without salt values will need to be recreated after updating to this version.

### Production Requirements

Before deploying to production:
- ✅ Password hashing implemented (SHA-256 with salt) - Consider upgrading to bcrypt/Argon2
- ⚠️ Add JWT tokens for stateless authentication
- ⚠️ Add session management and authorization
- ⚠️ Implement rate limiting
- ⚠️ Add comprehensive logging and monitoring
- ⚠️ Use proper SSL certificate
- ✅ Store encryption keys securely (`.bin` files)

## Database Schema

### users
- user_id (BIGINT, PK)
- username (VARCHAR(100), UNIQUE, NOT NULL)
- password (VARCHAR(500), NOT NULL) - SHA-256 hash (Base64 encoded)
- salt (VARCHAR(100), NOT NULL) - Random salt (Base64 encoded)
- created_at (TIMESTAMP)

### cases
- case_id (BIGINT, PK)
- case_name (VARCHAR)
- description (TEXT)
- created_at (TIMESTAMP)

### images
- image_id (BIGINT, PK)
- case_id (BIGINT, FK)
- filename (VARCHAR)
- filepath (VARCHAR)
- iv_base64 (VARCHAR)
- hmac_base64 (VARCHAR)
- uploaded_at (TIMESTAMP)

## License

This project is for educational purposes.

