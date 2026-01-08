package com.forensic.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * Service for managing key files (.bin)
 * Keys are stored as binary files (kept out of version control)
 */
@Service
public class KeyManagementService {

    @Value("${sam.file.aes.path:./config/keys.bin}")
    private String aesKeyFilePath;

    @Value("${sam.file.hmac.path:./config/hmac.bin}")
    private String hmacKeyFilePath;

    private static final int KEY_SIZE = 32; // 32 bytes for AES-256 and HMAC-SHA256

    /**
     * Reads the AES key from the .bin file
     * 
     * @return The AES-256 key as a byte array (32 bytes)
     * @throws Exception if key reading fails or key is invalid size
     */
    public byte[] getAesKey() throws Exception {
        return readKeyFromFile(aesKeyFilePath, "AES");
    }

    /**
     * Reads the HMAC key from the .bin file
     * 
     * @return The HMAC key as a byte array (32 bytes)
     * @throws Exception if key reading fails or key is invalid size
     */
    public byte[] getHmacKey() throws Exception {
        return readKeyFromFile(hmacKeyFilePath, "HMAC");
    }

    /**
     * Reads a key from a .bin file
     * 
     * @param filePath Path to the .bin file
     * @param keyType  Type of key (for error messages)
     * @return The key as a byte array (32 bytes)
     * @throws Exception if key reading fails or key is invalid size
     */
    private byte[] readKeyFromFile(String filePath, String keyType) throws Exception {
        Path keyFile = Paths.get(filePath);

        if (!Files.exists(keyFile)) {
            throw new IOException(keyType + " key file not found: " + filePath +
                    ". Please create it with your constant key.");
        }

        // Read key from file (stored as plaintext bytes)
        byte[] keyBytes = Files.readAllBytes(keyFile);

        // Validate key size
        if (keyBytes.length != KEY_SIZE) {
            throw new IllegalArgumentException(
                    "Invalid " + keyType + " key size in .bin file. Expected 32 bytes, got: " + keyBytes.length);
        }

        return keyBytes;
    }

    /**
     * Saves a key to .bin file
     * 
     * @param keyBytes The 32-byte key to save
     * @param filePath Path where to save the key
     * @param keyType  Type of key (for logging)
     */
    public void saveKey(byte[] keyBytes, String filePath, String keyType) throws Exception {
        // Validate key size
        if (keyBytes.length != KEY_SIZE) {
            throw new IllegalArgumentException(
                    keyType + " key must be exactly 32 bytes. Got: " + keyBytes.length);
        }

        // Ensure parent directory exists
        Path keyFile = Paths.get(filePath);
        Files.createDirectories(keyFile.getParent());

        // Write key to file
        Files.write(keyFile, keyBytes);

        System.out.println("✅ " + keyType + " key saved to: " + filePath);
    }

    /**
     * Validates that the key is the correct size for AES-256
     */
    public boolean validateKeySize(byte[] key) {
        return key != null && key.length == KEY_SIZE;
    }
}
