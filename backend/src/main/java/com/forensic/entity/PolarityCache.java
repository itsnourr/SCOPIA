package com.forensic.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.OffsetDateTime;

@Entity
@Table(name = "polarity_cache")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor 
public class PolarityCache {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String suspect;

    @Column(nullable = false)
    private String term;

    @Lob
    @Column(nullable = false)
    private String sentence;

    @Column(nullable = false, length = 20)
    private String polarity;

    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;
}