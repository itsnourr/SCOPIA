package com.forensic.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Table(name = "case_assignments", 
       uniqueConstraints = @UniqueConstraint(columnNames = {"case_id", "user_id"}))
@Data
@NoArgsConstructor
@AllArgsConstructor
public class CaseAssignment {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id; // surrogate key since composite PK is avoided in JPA best practice

    @Column(name = "case_id", nullable = false)
    private Integer caseId;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(length = 50) // e.g., 'admin', 'investigator', 'viewer'
    private String role;

    @Column(name = "assigned_at")
    private LocalDateTime assignedAt;

    @Column(name = "removed_at")
    private LocalDateTime removedAt;
}