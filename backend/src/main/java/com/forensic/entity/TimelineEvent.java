package com.forensic.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.OffsetDateTime;

@Entity
@Table(name = "timeline_events")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor 
public class TimelineEvent {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "source_doc_id", nullable = false)
    private String sourceDocId;

    @Lob
    @Column(name = "raw_text", nullable = false)
    private String rawText;

    @Column(name = "event_type", nullable = false)
    private String eventType;

    @Column(nullable = false)
    private OffsetDateTime timestamp;

    @Column(nullable = false)
    private Double confidence = 1.0;

    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;

    // Relationships
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "case_id", nullable = false)
    private Case caseEntity;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "suspect_id")
    private Suspect suspect; // nullable
}