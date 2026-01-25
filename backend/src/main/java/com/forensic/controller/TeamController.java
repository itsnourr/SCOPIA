package com.forensic.controller;

import com.forensic.dto.TeamDto;
import com.forensic.service.TeamService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/team")
@RequiredArgsConstructor
@CrossOrigin(origins = "http://localhost:3000")
public class TeamController {

    private final TeamService teamService;

    /**
     * Get all teams (all cases with their active members)
     */
    @GetMapping
    public ResponseEntity<List<TeamDto>> getAllTeams() {
        return ResponseEntity.ok(teamService.getAllTeams());
    }

    /**
     * Get a single team by caseId
     */
    @GetMapping("/{caseId}")
    public ResponseEntity<TeamDto> getTeamByCaseId(@PathVariable Long caseId) {
        return ResponseEntity.ok(teamService.getTeamByCaseId(caseId));
    }

    /**
     * Add a member to a case team
     */
    @PostMapping("/{caseId}/members/{userId}")
    public ResponseEntity<Void> addMember(
            @PathVariable Long caseId,
            @PathVariable Long userId
    ) {
        teamService.addMemberToTeam(caseId, userId);
        return ResponseEntity.ok().build();
    }

    /**
     * Remove a member from a case team (soft delete)
     */
    @DeleteMapping("/{caseId}/members/{userId}")
    public ResponseEntity<Void> removeMember(
            @PathVariable Long caseId,
            @PathVariable Long userId
    ) {
        teamService.removeMemberFromTeam(caseId, userId);
        return ResponseEntity.noContent().build();
    }
}
