package com.forensic.service;

import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.util.Base64;

/**
 * Service for password hashing using SHA-256 with salt
 * Each password gets a unique random salt stored in the database
 */
@Service
public class PasswordService {
    
    private static final String ALGORITHM = "SHA-256";
    private static final int SALT_LENGTH = 16; // 16 bytes = 128 bits
    
    /**
     * Generates a random salt for password hashing
     * @return Base64 encoded salt string
     */
    public String generateSalt() {
        SecureRandom random = new SecureRandom();
        byte[] saltBytes = new byte[SALT_LENGTH];
        random.nextBytes(saltBytes);
        return Base64.getEncoder().encodeToString(saltBytes);
    }
    
    /**
     * Hashes a password with a salt using SHA-256
     * @param password The plain text password
     * @param salt The salt (Base64 encoded)
     * @return Base64 encoded hash of (password + salt)
     * @throws NoSuchAlgorithmException if SHA-256 is not available
     */
    public String hashPassword(String password, String salt) throws NoSuchAlgorithmException {
        try {
            MessageDigest digest = MessageDigest.getInstance(ALGORITHM);
            
            // Combine password and salt
            String saltedPassword = password + salt;
            byte[] passwordBytes = saltedPassword.getBytes(StandardCharsets.UTF_8);
            
            // Hash the salted password
            byte[] hashBytes = digest.digest(passwordBytes);
            
            // Return Base64 encoded hash
            return Base64.getEncoder().encodeToString(hashBytes);
            
        } catch (NoSuchAlgorithmException e) {
            throw new NoSuchAlgorithmException("SHA-256 algorithm not available", e);
        }
    }
    
    /**
     * Verifies a password against a stored hash and salt
     * @param password The plain text password to verify
     * @param storedHash The stored password hash (Base64 encoded)
     * @param storedSalt The stored salt (Base64 encoded)
     * @return true if password matches, false otherwise
     */
    public boolean verifyPassword(String password, String storedHash, String storedSalt) {
        try {
            // Hash the provided password with the stored salt
            String computedHash = hashPassword(password, storedSalt);
            
            // Use constant-time comparison to prevent timing attacks
            return MessageDigest.isEqual(
                Base64.getDecoder().decode(storedHash),
                Base64.getDecoder().decode(computedHash)
            );
            
        } catch (Exception e) {
            return false;
        }
    }
}

