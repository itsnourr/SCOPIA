package com.forensic.controller;

import com.forensic.dto.CaseDetailsUpdateRequest;
import com.forensic.entity.Case;
import com.forensic.service.CaseService;
import com.forensic.repository.CaseRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List; 

@RestController
@RequestMapping("/api/case")
public class CaseController {

    @Autowired
    private CaseRepository caseRepository;
    
    @Autowired
    private CaseService caseService;

    // get case by id
    @GetMapping("/{id}")
    public ResponseEntity<?> getCaseById(@PathVariable Long id) {
        try {
            Case caseEntity = caseRepository.findById(id)
                    .orElseThrow(() -> new RuntimeException("Case not found with id: " + id));
            return ResponseEntity.ok(caseEntity);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error retrieving case: " + e.getMessage());
        }
    }

    @GetMapping("/all")
    public ResponseEntity<?> getAllCases() {
        try {
            List<Case> cases = caseRepository.findAll();
            return ResponseEntity.ok(cases);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error retrieving cases: " + e.getMessage());
        }
    }

    @GetMapping("/all/open")
    public ResponseEntity<?> getAllOpenCases() {
        try {
            List<Case> cases = caseService.listOpenCases();
            return ResponseEntity.ok(cases);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error retrieving cases: " + e.getMessage());
        }
    }

    @GetMapping("/all/archived")
    public ResponseEntity<?> getAllArchivedCases() {
        try {
            List<Case> cases = caseService.listArchivedCases();
            return ResponseEntity.ok(cases);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error retrieving cases: " + e.getMessage());
        }
    }

    @GetMapping("/all/open/{username}")
    public ResponseEntity<?> getOpenCasesByUsername(@PathVariable String username) {
        try {
            List<Case> cases = caseService.listOpenCasesByUsername(username);
            return ResponseEntity.ok(cases);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error retrieving cases: " + e.getMessage());
        }
    }

    @GetMapping("/all/archived/{username}")
    public ResponseEntity<?> getArchivedCasesByUsername(@PathVariable String username) {
        try {
            List<Case> cases = caseService.listArchivedCasesByUsername(username);
            return ResponseEntity.ok(cases);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error retrieving cases: " + e.getMessage());
        }
    }

    @PostMapping("/create")
    public ResponseEntity<?> createCase(@RequestBody Case caseEntity) {
        try {
            Case savedCase = caseRepository.save(caseEntity);
            return ResponseEntity.status(HttpStatus.CREATED).body(savedCase);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error creating case: " + e.getMessage());
        }
    }

    @PostMapping("/archive/{id}")
    public ResponseEntity<?> archiveCase(@PathVariable Long id) {
        try {
            caseService.archiveCase(id);
            return ResponseEntity.ok("Case archived successfully");
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error archiving case: " + e.getMessage());
        }
    }

    @PostMapping("/reopen/{id}")
    public ResponseEntity<?> reopenCase(@PathVariable Long id) {
        try {
            caseService.reopenCase(id);
            return ResponseEntity.ok("Case reopened successfully");
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error reopening case: " + e.getMessage());
        }
    }

    @PutMapping("/update/{id}")
    public ResponseEntity<?> updateCase(@PathVariable Long id, @RequestBody Case updatedCase) {
        try {
            Case existingCase = caseRepository.findById(id)
                    .orElseThrow(() -> new RuntimeException("Case not found with id: " + id));

            existingCase.setDescription(updatedCase.getDescription());
            existingCase.setStatus(updatedCase.getStatus());
            existingCase.setLocation(updatedCase.getLocation());
            existingCase.setCoordinates(updatedCase.getCoordinates());
            existingCase.setReportDate(updatedCase.getReportDate());
            existingCase.setCrimeTime(updatedCase.getCrimeTime());
            existingCase.setCaseKey(updatedCase.getCaseKey());

            Case savedCase = caseRepository.save(existingCase);
            return ResponseEntity.ok(savedCase);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error updating case: " + e.getMessage());
        }
    }

    @PutMapping("/update/details/{id}")
    public ResponseEntity<?> updateCaseDetails(
            @PathVariable Long id,
            @RequestBody CaseDetailsUpdateRequest request) {

        try {
            Case existingCase = caseRepository.findById(id)
                    .orElseThrow(() -> new RuntimeException("Case not found with id: " + id));

            // Only allowed fields
            existingCase.setLocation(request.getLocation());
            existingCase.setCoordinates(request.getCoordinates());
            existingCase.setReportDate(request.getReportDate());
            existingCase.setCrimeTime(request.getCrimeTime());

            Case savedCase = caseRepository.save(existingCase);
            return ResponseEntity.ok(savedCase);

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error updating case details: " + e.getMessage());
        }
    }
}
