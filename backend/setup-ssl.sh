#!/bin/bash

# SSL Certificate Generation Script for Forensic Image Storage System
# This script generates a self-signed certificate for HTTPS in development

echo "==================================="
echo "SSL Certificate Generation"
echo "==================================="
echo ""
echo "Generating PKCS12 keystore for Spring Boot HTTPS..."
echo ""

# Generate keystore
keytool -genkeypair -alias forensic \
  -keyalg RSA \
  -keysize 2048 \
  -storetype PKCS12 \
  -keystore src/main/resources/keystore.p12 \
  -validity 365 \
  -storepass forensic123 \
  -dname "CN=localhost, OU=Forensic, O=ForensicSystem, L=City, ST=State, C=US"

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ SSL certificate generated successfully!"
    echo "  Location: src/main/resources/keystore.p12"
    echo "  Password: forensic123"
    echo ""
    echo "⚠ NOTE: This is a self-signed certificate for DEVELOPMENT only."
    echo "  For production, use a CA-signed certificate."
else
    echo ""
    echo "✗ Error generating SSL certificate"
    exit 1
fi

