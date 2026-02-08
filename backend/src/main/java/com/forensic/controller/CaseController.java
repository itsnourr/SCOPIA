package com.forensic.controller;

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
}
