package com.forensic.repository;

import com.forensic.entity.CaseAssignment;
import com.forensic.entity.Case;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

public interface CaseAssignmentRepository extends JpaRepository<CaseAssignment, Long> {

    // add this findByStatusAndAssignedTo(String status, String assignedTo)
    @Query("""
        SELECT c 
        FROM CaseAssignment ca 
        JOIN Case c ON ca.caseId = c.id 
        WHERE c.status = :status 
          AND ca.userId = :assignedTo 
          AND ca.removedAt IS NULL
    """)
    // return list<case> instead
    List<Case> findByStatusAndAssignedTo(String status, Long assignedTo);
    
    // Active members of a specific case
    @Query("""
        SELECT ca 
        FROM CaseAssignment ca 
        WHERE ca.caseId = :caseId 
          AND ca.removedAt IS NULL
    """)
    List<CaseAssignment> findActiveByCaseId(Long caseId);

    // Active assignment for a user in a case
    @Query("""
        SELECT ca 
        FROM CaseAssignment ca 
        WHERE ca.caseId = :caseId 
          AND ca.userId = :userId 
          AND ca.removedAt IS NULL
    """)
    Optional<CaseAssignment> findActiveByCaseIdAndUserId(Long caseId, Long userId);

    // Any assignment (active or revoked)
    Optional<CaseAssignment> findByCaseIdAndUserId(Long caseId, Long userId);

    // All active assignments (used for getAllTeams)
    @Query("""
        SELECT ca 
        FROM CaseAssignment ca 
        WHERE ca.removedAt IS NULL
    """)
    List<CaseAssignment> findAllActive();

    @Modifying
    @Transactional
    @Query("""
        UPDATE CaseAssignment 
        SET removedAt = CURRENT_TIMESTAMP 
        WHERE caseId = :caseId 
          AND userId = :userId 
          AND removedAt IS NULL
    """)
    void revokeUserFromCaseTeam(Long caseId, Long userId);
}
