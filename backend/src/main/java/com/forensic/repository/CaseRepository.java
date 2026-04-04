package com.forensic.repository;

import com.forensic.entity.Case;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import java.util.List;
import java.util.Optional;

@Repository
public interface CaseRepository extends JpaRepository<Case, Long> {
    List<Case> findByStatus(String status);
    Page<Case> findByStatus(String status, Pageable pageable);
    List<Case> findByStatusIgnoreCase(String status);
    List<Case> findByCaseIdInAndStatus(List<Long> caseIds, String status);
    Optional<Case> findByCaseKey(String caseKey);
    // List<Case> findByStatusAndAssignedTo(String status, String assignedTo);
}

