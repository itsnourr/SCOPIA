package com.forensic.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.crypto.Cipher;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.security.SecureRandom;
import java.util.Arrays;
import java.util.Base64;

@Service
public class CryptoService {
    
    @Autowired
    private KeyManagementService keyManagementService;
    
    @Value("${app.crypto.use.sam.file:true}")
    private boolean useSamFile;
    
    @Value("${app.crypto.aes.key:}")
    private String aesKeyString;
    
    private byte[] cachedKeyBytes = null; // Cache the decrypted key
    
    private static final String ALGORITHM = "AES";
    private static final String TRANSFORMATION = "AES/CBC/PKCS5Padding";
    private static final int IV_SIZE = 16; // AES uses 16-byte IV
    private static final int KEY_SIZE = 32; // AES-256 uses 32-byte key
    
    /**
     * Gets the AES key either from .bin file or fallback to application.properties
     * @return AES-256 key bytes (32 bytes)
     * @throws Exception if key cannot be loaded or is invalid size
     */
    private byte[] getKeyBytes() throws Exception {
        // Return cached key if available
        if (cachedKeyBytes != null) {
            return cachedKeyBytes;
        }
        
        byte[] keyBytes;
        
        if (useSamFile) {
            // Load from .bin file
            System.out.println("🔐 Loading AES key from .bin file...");
            keyBytes = keyManagementService.getAesKey();
            System.out.println("✅ Key loaded successfully from .bin file");
        } else {
            // Fallback to hardcoded key from properties (legacy mode)
            System.out.println("⚠️  WARNING: Using hardcoded key from application.properties");
            System.out.println("   For better security, use .bin file (set app.crypto.use.sam.file=true)");
            keyBytes = aesKeyString.getBytes();
        }
        
        // Validate key size
        if (keyBytes.length != KEY_SIZE) {
            throw new IllegalArgumentException(
                "AES-256 key must be exactly 32 bytes. Current size: " + keyBytes.length + " bytes"
            );
        }
        
        // Cache the key for future use
        cachedKeyBytes = keyBytes;
        
        return keyBytes;
    }
    
    /**
     * Encrypts an image file using AES-256 cipher in CBC mode
     * Generates a random IV and prepends it to the ciphertext
     * @param inputFilePath Path to the input image file
     * @param outputFilePath Path where encrypted file will be saved
     * @param ivBase64Holder Single-element array to return the IV in Base64 format
     * @throws Exception if encryption fails
     */
    public void encrypt(String inputFilePath, String outputFilePath, String[] ivBase64Holder) throws Exception {
        // Generate random IV
        SecureRandom random = new SecureRandom();
        byte[] iv = new byte[IV_SIZE];
        random.nextBytes(iv);
        
        // Store IV in Base64 format for database
        if (ivBase64Holder != null && ivBase64Holder.length > 0) {
            ivBase64Holder[0] = Base64.getEncoder().encodeToString(iv);
        }
        
        // Get AES-256 key (from .bin file or properties)
        byte[] keyBytes = getKeyBytes();
        SecretKeySpec keySpec = new SecretKeySpec(keyBytes, ALGORITHM);
        
        // Initialize cipher
        Cipher cipher = Cipher.getInstance(TRANSFORMATION);
        IvParameterSpec ivSpec = new IvParameterSpec(iv);
        cipher.init(Cipher.ENCRYPT_MODE, keySpec, ivSpec);
        
        // Read input file
        FileInputStream inputStream = new FileInputStream(inputFilePath);
        byte[] inputBytes = inputStream.readAllBytes();
        inputStream.close();
        
        // Encrypt the data
        byte[] encryptedBytes = cipher.doFinal(inputBytes);
        
        // Write IV + encrypted data to output file
        FileOutputStream outputStream = new FileOutputStream(outputFilePath);
        outputStream.write(iv); // Write IV first
        outputStream.write(encryptedBytes); // Write encrypted data
        outputStream.close();
    }
    
    /**
     * Decrypts an image file using AES-256 cipher in CBC mode
     * Extracts the IV from the beginning of the file
     * @param encryptedFilePath Path to the encrypted file (with IV prepended)
     * @return Decrypted image bytes
     * @throws Exception if decryption fails
     */
    public byte[] decrypt(String encryptedFilePath) throws Exception {
        // Read encrypted file
        FileInputStream inputStream = new FileInputStream(encryptedFilePath);
        byte[] fileBytes = inputStream.readAllBytes();
        inputStream.close();
        
        if (fileBytes.length < IV_SIZE) {
            throw new IllegalArgumentException("Invalid encrypted file: too small");
        }
        
        // Extract IV (first 16 bytes)
        byte[] iv = Arrays.copyOfRange(fileBytes, 0, IV_SIZE);
        
        // Extract encrypted data (remaining bytes)
        byte[] encryptedData = Arrays.copyOfRange(fileBytes, IV_SIZE, fileBytes.length);
        
        // Get AES-256 key (from .bin file or properties)
        byte[] keyBytes = getKeyBytes();
        SecretKeySpec keySpec = new SecretKeySpec(keyBytes, ALGORITHM);
        
        // Initialize cipher for decryption
        Cipher cipher = Cipher.getInstance(TRANSFORMATION);
        IvParameterSpec ivSpec = new IvParameterSpec(iv);
        cipher.init(Cipher.DECRYPT_MODE, keySpec, ivSpec);
        
        // Decrypt and return
        return cipher.doFinal(encryptedData);
    }
    
    /**
     * Reads encrypted file bytes for HMAC generation
     * @param encryptedFilePath Path to the encrypted file
     * @return Encrypted file bytes (including IV)
     * @throws IOException if file reading fails
     */
    public byte[] readEncryptedFile(String encryptedFilePath) throws IOException {
        FileInputStream inputStream = new FileInputStream(encryptedFilePath);
        byte[] fileBytes = inputStream.readAllBytes();
        inputStream.close();
        return fileBytes;
    }
}

