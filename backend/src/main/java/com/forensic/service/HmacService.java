package com.forensic.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.security.InvalidKeyException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Base64;

@Service
public class HmacService {
    
    @Autowired
    private KeyManagementService keyManagementService;
    
    private static final String HMAC_ALGORITHM = "HmacSHA256";
    private byte[] cachedHmacKey = null; // Cache the key
    private String cachedKeyHash = null; // Track key changes
    
    /**
     * Gets the HMAC key (loaded from .bin file on first use)
     * Detects if key has changed and clears cache
     */
    private byte[] getHmacKey() throws Exception {
        byte[] currentKey = keyManagementService.getHmacKey();
        String currentKeyHash = java.util.Arrays.toString(currentKey);
        
        // Check if key has changed
        if (cachedHmacKey != null && !currentKeyHash.equals(cachedKeyHash)) {
            System.err.println("⚠️ WARNING: HMAC key has changed! Clearing cache.");
            System.err.println("   This will cause HMAC verification to fail for images uploaded with the old key.");
            cachedHmacKey = null;
            cachedKeyHash = null;
        }
        
        if (cachedHmacKey == null) {
            System.out.println("🔐 Loading HMAC key from .bin file...");
            cachedHmacKey = currentKey;
            cachedKeyHash = currentKeyHash;
            System.out.println("✅ HMAC key loaded successfully");
        }
        return cachedHmacKey;
    }
    
    /**
     * Generates HMAC for the encrypted image bytes
     * @param data The encrypted image bytes (including IV)
     * @return Base64 encoded HMAC
     * @throws NoSuchAlgorithmException if HMAC algorithm not available
     * @throws InvalidKeyException if key is invalid
     */
    public String generateHmac(byte[] data) throws Exception {
        Mac mac = Mac.getInstance(HMAC_ALGORITHM);
        SecretKeySpec secretKeySpec = new SecretKeySpec(
            getHmacKey(), 
            HMAC_ALGORITHM
        );
        mac.init(secretKeySpec);
        byte[] hmacBytes = mac.doFinal(data);
        return Base64.getEncoder().encodeToString(hmacBytes);
    }
    
    /**
     * Verifies if the stored HMAC matches the newly generated HMAC
     * @param data The encrypted image bytes (including IV)
     * @param storedHmac The stored HMAC in Base64 format
     * @return true if HMAC matches, false otherwise
     */
    public boolean verifyHmac(byte[] data, String storedHmac) {
        try {
            if (data == null || storedHmac == null || storedHmac.isEmpty()) {
                System.err.println("⚠️ HMAC verification failed: null data or stored HMAC");
                return false;
            }
            
            String newHmac = generateHmac(data);
            boolean isValid = MessageDigest.isEqual(
                Base64.getDecoder().decode(storedHmac),
                Base64.getDecoder().decode(newHmac)
            );
            
            if (!isValid) {
                System.err.println("⚠️ HMAC mismatch!");
                System.err.println("   Stored HMAC: " + storedHmac);
                System.err.println("   Generated HMAC: " + newHmac);
            }
            
            return isValid;
        } catch (Exception e) {
            System.err.println("❌ HMAC verification error: " + e.getMessage());
            e.printStackTrace();
            return false;
        }
    }
}

