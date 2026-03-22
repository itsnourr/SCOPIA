package com.forensic.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.OffsetDateTime;

@Entity
@Table(
    name = "chat_memory",
    uniqueConstraints = @UniqueConstraint(
        name = "uq_chat_memory_user_key",
        columnNames = {"user_id", "key"}
    )
)
@Getter @Setter @NoArgsConstructor @AllArgsConstructor
public class ChatMemory {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private String userId;

    @Column(nullable = false)
    private String key;

    @Lob
    @Column(nullable = false)
    private String value;

    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private OffsetDateTime updatedAt;
}