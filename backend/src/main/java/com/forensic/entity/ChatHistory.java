package com.forensic.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.OffsetDateTime;

@Entity
@Table(name = "chat_history")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor 
public class ChatHistory {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private String userId;

    @Lob
    @Column(nullable = false)
    private String message;

    @Column(name = "is_user", nullable = false)
    private boolean isUser;

    @Column(name = "case_id")
    private Long caseId;

    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;
}