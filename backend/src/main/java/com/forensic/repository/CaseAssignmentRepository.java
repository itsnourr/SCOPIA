package com.forensic.repository;

import com.forensic.entity.CaseAssignment;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

public interface CaseAssignmentRepository extends JpaRepository<CaseAssignment, Long> {
    List<CaseAssignment> findByCaseId(Integer caseId);
    
    Optional<CaseAssignment> findByCaseIdAndUserId(Integer caseId, Long userId);
    
    @Modifying
    @Transactional
    @Query("UPDATE CaseAssignment SET removedAt = CURRENT_TIMESTAMP WHERE caseId = :caseId AND userId = :userId AND removedAt IS NULL")
    void revokeUserFromCaseTeam(Integer caseId, Long userId);
}