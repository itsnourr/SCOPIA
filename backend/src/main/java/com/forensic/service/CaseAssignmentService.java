package com.forensic.service;

import com.forensic.entity.CaseAssignment;
import com.forensic.repository.CaseAssignmentRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class CaseAssignmentService {

    private final CaseAssignmentRepository assignmentRepository;

    @Transactional
    public void assignTeamToCase(Integer caseId, Integer teamAssignedId) {
        // Assuming "team_assigned_id" is stored directly in CaseEntity
        // This might be handled in CaseService instead if it's a simple field update
        throw new UnsupportedOperationException("Handled via CaseEntity update");
    }

    @Transactional
    public void addUserToCaseTeam(Integer caseId, Long userId, String role) {
        Optional<CaseAssignment> existing = assignmentRepository.findByCaseIdAndUserId(caseId, userId);
        if (existing.isPresent() && existing.get().getRemovedAt() == null) {
            throw new RuntimeException("User already assigned to this case");
        }
        CaseAssignment assignment = new CaseAssignment();
        assignment.setCaseId(caseId);
        assignment.setUserId(userId);
        assignment.setRole(role != null ? role : "viewer");
        assignment.setAssignedAt(LocalDateTime.now());
        assignment.setRemovedAt(null);
        assignmentRepository.save(assignment);
    }

    @Transactional
    public void revokeUserFromCaseTeam(Integer caseId, Long userId) {
        assignmentRepository.revokeUserFromCaseTeam(caseId, userId);
    }

    public List<CaseAssignment> getAssignmentsForCase(Integer caseId) {
        return assignmentRepository.findByCaseId(caseId);
    }
}