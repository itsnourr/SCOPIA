package com.forensic.controller;

import com.forensic.dto.AuthRequest;
import com.forensic.dto.AuthResponse;
import com.forensic.entity.User;
import com.forensic.repository.UserRepository;
import com.forensic.service.PasswordService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Optional;

/**
 * User Controller with secure password hashing
 * Passwords are hashed using SHA-256 with unique salt per user
 */
@RestController
@RequestMapping("/api/user")
public class UserController {
    
    @Autowired
    private UserRepository userRepository;
    
    @Autowired
    private PasswordService passwordService;
    
    /**
     * POST /api/user/signup
     * Secure signup - hashes password with SHA-256 and unique salt
     */
    @PostMapping("/signup")
    public ResponseEntity<?> signup(@RequestBody AuthRequest request) {
        try {
            // Check if username already exists
            if (userRepository.existsByUsername(request.getUsername())) {
                return ResponseEntity.status(HttpStatus.CONFLICT)
                        .body(new AuthResponse(null, null, "Username already exists"));
            }
            
            // Validate input
            if (request.getUsername() == null || request.getUsername().trim().isEmpty()) {
                return ResponseEntity.badRequest()
                        .body(new AuthResponse(null, null, "Username is required"));
            }
            
            if (request.getPassword() == null || request.getPassword().trim().isEmpty()) {
                return ResponseEntity.badRequest()
                        .body(new AuthResponse(null, null, "Password is required"));
            }
            
            // Generate unique salt for this user
            String salt = passwordService.generateSalt();
            
            // Hash the password with the salt
            String hashedPassword = passwordService.hashPassword(request.getPassword(), salt);
            
            // Create new user with hashed password and salt
            User newUser = new User();
            newUser.setUsername(request.getUsername());
            newUser.setPassword(hashedPassword);
            newUser.setSalt(salt);
            
            User savedUser = userRepository.save(newUser);
            
            return ResponseEntity.status(HttpStatus.CREATED)
                    .body(new AuthResponse(
                            savedUser.getUserId(),
                            savedUser.getUsername(),
                            "User registered successfully"
                    ));
            
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(new AuthResponse(null, null, "Error during signup: " + e.getMessage()));
        }
    }
    
    /**
     * POST /api/user/login
     * Secure login - verifies password hash with stored salt
     */
    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody AuthRequest request) {
        try {
            // Find user by username
            Optional<User> userOptional = userRepository.findByUsername(request.getUsername());
            
            if (userOptional.isEmpty()) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                        .body(new AuthResponse(null, null, "Invalid username or password"));
            }
            
            User user = userOptional.get();
            
            // Verify password using stored hash and salt
            boolean isValid = passwordService.verifyPassword(
                    request.getPassword(),
                    user.getPassword(),
                    user.getSalt()
            );
            
            if (!isValid) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                        .body(new AuthResponse(null, null, "Invalid username or password"));
            }
            
            return ResponseEntity.ok(new AuthResponse(
                    user.getUserId(),
                    user.getUsername(),
                    "Login successful"
            ));
            
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(new AuthResponse(null, null, "Error during login: " + e.getMessage()));
        }
    }
}

