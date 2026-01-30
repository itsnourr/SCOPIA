package com.forensic.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Table(name = "links")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Link {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "link_id")
    private Long linkId;

    @Column(name = "case_key", nullable = false, length = 50)
    private String caseKey;

    @Column(name = "node_id_from", nullable = false)
    private Long nodeIdFrom;

    @Column(name = "node_id_to", nullable = false)
    private Long nodeIdTo;

    @Column(name = "link_desc", columnDefinition = "TEXT")
    private String linkDesc;

    @Column(name = "is_bidirectional")
    private Boolean bidirectional;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}