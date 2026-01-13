package com.forensic.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Table(name = "cases")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Case {
    
    @Id 
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "case_id")
    private Long caseId;
    
    @Column(name = "case_name", nullable = false, length = 200)
    private String caseName;
    
    @Column(columnDefinition = "TEXT")
    private String description;
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(length = 20) // e.g., 'open' or 'archived'
    private String status;

    @Column(name = "team_assigned_id")
    private Long teamAssignedId;

    @Column(length = 255)
    private String location;

    @Column(length = 100)
    private String coordinates;

    @Column(name = "report_date")
    private LocalDateTime reportDate;

    @Column(name = "crime_time")
    private LocalDateTime crimeTime;
    
    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}

