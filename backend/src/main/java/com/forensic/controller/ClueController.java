package com.forensic.controller;

import com.forensic.entity.Clue;
import com.forensic.repository.ClueRepository;
import com.forensic.service.ClueService;
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
@RequestMapping("/api/clue")
public class ClueController {

    @Autowired
    private ClueRepository clueRepository;

    @Autowired
    private ClueService clueService;

    /**
     * GET /api/clue/all
     * Returns all clues
     */
    @GetMapping("/all")
    public ResponseEntity<?> getAllClues() {
        try {
            List<Clue> clues = clueRepository.findAll();
            return ResponseEntity.ok(clues);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error retrieving clues: " + e.getMessage());
        }
    }

    /**
     * GET /api/clue/case/{caseId}
     * Returns all clues for a specific case
     */
    @GetMapping("/case/{caseId}")
    public ResponseEntity<?> getCluesByCaseId(@PathVariable Long caseId) {
        try {
            List<Clue> clues = clueService.getCluesByCaseIdWithPagination(caseId, Pageable.unpaged()).getContent();
            return ResponseEntity.ok(clues);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error retrieving clues for case: " + e.getMessage());
        }
    }

    // add clue to a case
    @PostMapping("/case/{caseId}")
    public ResponseEntity<?> addClueToCase(@PathVariable Long caseId, @RequestBody Clue clue) {
        try {
            clue.setCaseId(caseId); // Ensure the clue is associated with the correct case
            Clue savedClue = clueService.addClue(clue);
            return ResponseEntity.status(HttpStatus.CREATED).body(savedClue);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error adding clue to case: " + e.getMessage());
        }
    }

    /**
     * GET /api/clue/{id}
     * Returns a clue by ID
     */
    @GetMapping("/{id}")
    public ResponseEntity<?> getClueById(@PathVariable Long id) {
        try {
            Optional<Clue> clue = clueRepository.findById(id);

            if (clue.isEmpty()) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body("Clue not found with id: " + id);
            }

            return ResponseEntity.ok(clue.get());

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error retrieving clue: " + e.getMessage());
        }
    }

    @PostMapping("/create/case/{caseId}")
    public ResponseEntity<?> createClue(@PathVariable Long caseId, @RequestBody Clue clue) {
        try {
            clue.setCaseId(caseId);
            Clue savedClue = clueRepository.save(clue);
            return ResponseEntity.status(HttpStatus.CREATED).body(savedClue);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error creating clue: " + e.getMessage());
        }
    }

    @PostMapping("/create/rover/{caseId}")
    public ResponseEntity<?> addRoverCluesByBulk(@PathVariable Long caseId, @RequestBody List<Clue> clues) {
        try {
            clueService.addRoverCluesByBulk(caseId, clues);
            return ResponseEntity.status(HttpStatus.CREATED).body("Rover clues added successfully");
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error adding rover clues: " + e.getMessage());
        }
    }

    @PutMapping("/update/{id}")
    public ResponseEntity<?> updateClue(
            @PathVariable Long id,
            @RequestBody Clue updatedClue) {

        try {
            Optional<Clue> existingClueOpt = clueRepository.findById(id);

            if (existingClueOpt.isEmpty()) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body("Clue not found with id: " + id);
            }

            Clue existingClue = existingClueOpt.get();

            // Update allowed fields
            existingClue.setType(updatedClue.getType());
            existingClue.setCategory(updatedClue.getCategory());
            existingClue.setPickerId(updatedClue.getPickerId());
            existingClue.setClueDesc(updatedClue.getClueDesc());
            existingClue.setCoordinates(updatedClue.getCoordinates());

            Clue savedClue = clueRepository.save(existingClue);
            return ResponseEntity.ok(savedClue);

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error updating clue: " + e.getMessage());
        }
    }

    /**
     * DELETE /api/clue/delete/{id}
     * Deletes a clue
     */
    @DeleteMapping("/delete/{id}")
    public ResponseEntity<?> deleteClue(@PathVariable Long id) {
        try {
            if (!clueRepository.existsById(id)) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body("Clue not found with id: " + id);
            }

            clueRepository.deleteById(id);
            return ResponseEntity.ok("Clue deleted successfully");

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error deleting clue: " + e.getMessage());
        }
    }
}
