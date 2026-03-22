package com.forensic.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.OffsetDateTime;

@Entity
@Table(name = "analysis_results")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor 
public class AnalysisResult {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "score_float", nullable = false)
    private Double scoreFloat;

    @Lob
    @Column(name = "matched_clues_json", nullable = false)
    private String matchedCluesJson; // store JSON as string

    @Column(name = "run_at", nullable = false, updatable = false)
    private OffsetDateTime runAt;

    // Relationships
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "case_id", nullable = false)
    private Case caseEntity;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "suspect_id", nullable = false)
    private Suspect suspect;
}