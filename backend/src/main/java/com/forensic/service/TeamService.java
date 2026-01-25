package com.forensic.service;

import com.forensic.dto.TeamDto;
import com.forensic.entity.CaseAssignment;
import com.forensic.repository.CaseAssignmentRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class TeamService {

    private final CaseAssignmentRepository caseAssignmentRepository;

    /**
     * Get all teams (group active assignments by caseId)
     */
    public List<TeamDto> getAllTeams() {

        List<CaseAssignment> activeAssignments =
                caseAssignmentRepository.findAllActive();

        Map<Long, List<Long>> teamsMap =
                activeAssignments.stream()
                        .collect(Collectors.groupingBy(
                                CaseAssignment::getCaseId,
                                Collectors.mapping(
                                        CaseAssignment::getUserId,
                                        Collectors.toList()
                                )
                        ));

        return teamsMap.entrySet()
                .stream()
                .map(e -> new TeamDto(e.getKey(), e.getValue()))
                .toList();
    }

    /**
     * Get one team by caseId
     */
    public TeamDto getTeamByCaseId(Long caseId) {

        List<Long> userIds = caseAssignmentRepository
                .findActiveByCaseId(caseId)
                .stream()
                .map(CaseAssignment::getUserId)
                .toList();

        return new TeamDto(caseId, userIds);
    }

    /**
     * Add member to team
     */
    @Transactional
    public void addMemberToTeam(Long caseId, Long userId) {

        Optional<CaseAssignment> existing =
                caseAssignmentRepository.findByCaseIdAndUserId(caseId, userId);

        if (existing.isPresent()) {
            CaseAssignment assignment = existing.get();

            if (assignment.getRemovedAt() == null) {
                return; // already active
            }

            assignment.setRemovedAt(null);
            assignment.setAssignedAt(LocalDateTime.now());
            caseAssignmentRepository.save(assignment);

        } else {
            CaseAssignment newAssignment = new CaseAssignment();
            newAssignment.setCaseId(caseId);
            newAssignment.setUserId(userId);
            newAssignment.setAssignedAt(LocalDateTime.now());
            newAssignment.setRemovedAt(null);

            caseAssignmentRepository.save(newAssignment);
        }
    }

    /**
     * Remove member from team (soft delete)
     */
    @Transactional
    public void removeMemberFromTeam(Long caseId, Long userId) {
        caseAssignmentRepository.revokeUserFromCaseTeam(caseId, userId);
    }
}
