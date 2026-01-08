package com.forensic.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * User entity with secure password hashing
 * Passwords are hashed using SHA-256 with unique salt per user
 */
@Entity
@Table(name = "users")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class User {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "user_id")
    private Long userId;
    
    @Column(unique = true, nullable = false, length = 100)
    private String username;
    
    @Column(nullable = false, length = 500)
    private String password; // SHA-256 hash (Base64 encoded)
    
    @Column(nullable = false, length = 100)
    private String salt; // Random salt for password hashing (Base64 encoded)
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;
    
    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}

