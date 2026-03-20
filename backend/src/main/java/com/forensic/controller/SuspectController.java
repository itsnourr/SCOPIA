package com.forensic.controller;

import com.forensic.entity.Suspect;
import com.forensic.repository.SuspectRepository;
import com.forensic.service.SuspectService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Optional;
// import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

@CrossOrigin(origins = "http://localhost:5173")
@RestController
@RequestMapping("/api/suspect")
public class SuspectController {

    @Autowired
    private SuspectRepository SuspectRepository;

    @Autowired
    private SuspectService SuspectService;

    /**
     * GET /api/Suspect/all
     * Returns all Suspects
     */
    @GetMapping("/all")
    public ResponseEntity<?> getAllSuspects() {
        try {
            List<Suspect> Suspects = SuspectRepository.findAll();
            return ResponseEntity.ok(Suspects);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error retrieving Suspects: " + e.getMessage());
        }
    }

    /**
     * GET /api/Suspect/case/{caseId}
     * Returns all Suspects for a specific case
     */
    @GetMapping("/case/{caseId}")
    public ResponseEntity<?> getSuspectsByCaseId(@PathVariable Long caseId) {
        try {
            List<Suspect> Suspects = SuspectService.getSuspectsByCaseIdWithPagination(caseId, Pageable.unpaged()).getContent();
            return ResponseEntity.ok(Suspects);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error retrieving Suspects for case: " + e.getMessage());
        }
    }

    // add Suspect to a case
    @PostMapping("/case/{caseId}")
    public ResponseEntity<?> addSuspectToCase(@PathVariable Long caseId, @RequestBody Suspect Suspect) {
        try {
            Suspect.setCaseId(caseId); // Ensure the Suspect is associated with the correct case
            Suspect savedSuspect = SuspectService.addSuspect(Suspect);
            return ResponseEntity.status(HttpStatus.CREATED).body(savedSuspect);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error adding Suspect to case: " + e.getMessage());
        }
    }

    /**
     * GET /api/Suspect/{id}
     * Returns a Suspect by ID
     */
    @GetMapping("/{id}")
    public ResponseEntity<?> getSuspectById(@PathVariable Long id) {
        try {
            Optional<Suspect> Suspect = SuspectRepository.findById(id);

            if (Suspect.isEmpty()) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body("Suspect not found with id: " + id);
            }

            return ResponseEntity.ok(Suspect.get());

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error retrieving Suspect: " + e.getMessage());
        }
    }

    /**
     * POST /api/Suspect/create
     * Creates a new Suspect
     */
    @PostMapping("/create")
    public ResponseEntity<?> createSuspect(@RequestBody Suspect Suspect) {
        try {
            Suspect savedSuspect = SuspectRepository.save(Suspect);
            return ResponseEntity.status(HttpStatus.CREATED).body(savedSuspect);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error creating Suspect: " + e.getMessage());
        }
    }
    // add Suspect to case given id
    @PostMapping("/create/case/{caseId}")
    public ResponseEntity<?> createSuspectToCase(@PathVariable Long caseId, @RequestBody Suspect Suspect) {
        try {
            Suspect.setCaseId(caseId);
            Suspect savedSuspect = SuspectRepository.save(Suspect);
            return ResponseEntity.status(HttpStatus.CREATED).body(savedSuspect);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error creating Suspect: " + e.getMessage());
        }
    }
    
    @PutMapping("/update/{id}")
    public ResponseEntity<?> updateSuspect(
            @PathVariable Long id,
            @RequestBody Suspect updatedSuspect) {

        try {
            Optional<Suspect> existingSuspectOpt = SuspectRepository.findById(id);

            if (existingSuspectOpt.isEmpty()) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body("Suspect not found with id: " + id);
            }

            Suspect existingSuspect = existingSuspectOpt.get();

            // Update allowed fields
            existingSuspect.setFullName(updatedSuspect.getFullName());
            existingSuspect.setAlias(updatedSuspect.getAlias());
            existingSuspect.setDateOfBirth(updatedSuspect.getDateOfBirth());
            existingSuspect.setNationality(updatedSuspect.getNationality());
            existingSuspect.setNotes(updatedSuspect.getNotes());

            Suspect savedSuspect = SuspectRepository.save(existingSuspect);
            return ResponseEntity.ok(savedSuspect);

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error updating Suspect: " + e.getMessage());
        }
    }

    /**
     * DELETE /api/Suspect/delete/{id}
     * Deletes a Suspect
     */
    @DeleteMapping("/delete/{id}")
    public ResponseEntity<?> deleteSuspect(@PathVariable Long id) {
        try {
            if (!SuspectRepository.existsById(id)) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body("Suspect not found with id: " + id);
            }

            SuspectRepository.deleteById(id);
            return ResponseEntity.ok("Suspect deleted successfully");

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error deleting Suspect: " + e.getMessage());
        }
    }
}
